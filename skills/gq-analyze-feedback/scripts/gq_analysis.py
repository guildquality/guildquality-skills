#!/usr/bin/env python3
"""Bounded arithmetic on retrieved survey records; no network or credential access."""
import argparse
import csv
import hashlib
import io
from calendar import monthrange
from decimal import Decimal, InvalidOperation
from datetime import date, datetime, timezone as datetime_timezone
from fractions import Fraction
import json
import math
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class CalculationError(ValueError):
    pass


def source_timestamp(value):
    """Parse an actual aware source instant; never invent a time or offset."""
    text = str(value)
    for suffix, offset in ((" EDT", "-04:00"), (" EST", "-05:00"), (" UTC", "+00:00"), (" GMT", "+00:00")):
        if text.endswith(suffix):
            text = text[:-len(suffix)] + offset
            break
    try:
        instant = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if instant.tzinfo is None:
            raise ValueError()
        return instant
    except ValueError:
        raise CalculationError("Timestamp needs a valid explicit offset or supported source timezone.") from None


def local_day(value, timezone):
    if not value:
        return None
    text = str(value)
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return date.fromisoformat(text)
        return source_timestamp(value).astimezone(ZoneInfo(timezone)).date()
    except (ValueError, ZoneInfoNotFoundError):
        raise CalculationError("Unsupported date/timezone in selected source records.") from None


def selection_id(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)) or not re.fullmatch(r"[1-9][0-9]{0,17}", str(value)):
        raise CalculationError("Latest-in-period selection needs unambiguous positive numeric survey and contact IDs.")
    return int(value)


def latest_completed_per_contact(rows, complete):
    """Choose within the already filtered cohort, before question eligibility."""
    groups = {}
    for row in rows:
        identifiers = []
        if "contact" in row:
            if not isinstance(row["contact"], dict) or "id" not in row["contact"]:
                raise CalculationError("Latest-in-period selection requires a stable contact ID on every relevant completed survey.")
            identifiers.append(selection_id(row["contact"]["id"]))
        if "contactId" in row:
            identifiers.append(selection_id(row["contactId"]))
        if not identifiers or len(set(identifiers)) != 1:
            raise CalculationError("Latest-in-period selection requires matching, nonmissing contact IDs.")
        contact = identifiers[0]
        key = (source_timestamp(row["endedAt"]), selection_id(row["id"]))
        group = groups.setdefault(contact, {"rows": [], "winner": row, "key": key})
        group["rows"].append(row)
        if key > group["key"]:
            group.update(winner=row, key=key)
    winners = sorted((group["winner"] for group in groups.values()), key=lambda row: selection_id(row["id"]))
    metadata = {
        "selection_policy": "Latest completed survey per supplied stable contact ID within the selected period, after import policy; not the app's global-latest selection",
        "selection_complete": complete is True,
        "selection_coverage_basis": "Completeness applies only to the supplied relevant source queries, not undiscovered account history or locations",
        "selection_input_completed_count": len(rows),
        "selection_contact_count": len(groups),
        "selection_excluded_older_count": len(rows) - len(winners),
        "selection_source_ids": [row["id"] for row in winners],
        "selection_tie_break": "Latest aware endedAt instant, then larger numeric survey ID",
        "selection_group_counts": [{"contact_id": contact, "completed_survey_count": len(group["rows"]),
                                    "source_ids": sorted((row["id"] for row in group["rows"]), key=selection_id),
                                    "selected_source_id": group["winner"]["id"],
                                    "selected_ended_at": group["winner"]["endedAt"]}
                                   for contact, group in sorted(groups.items())],
    }
    return winners, metadata


def numeric_rating(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        if not re.fullmatch(r"(?:10|[0-9])(?:\.0+)?", value.strip()):
            return None
        value = float(value)
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value != int(value) or not 0 <= value <= 10:
        return None
    return int(value)


def contact_identity(row):
    """Normalize only verified numeric identity aliases; never guess from names."""
    values, unknown = [], None
    if "contact" in row:
        contact = row["contact"]
        if not isinstance(contact, dict) or "id" not in contact:
            unknown = "missing" if contact is None or contact == {} else "invalid"
        else:
            values.append(contact["id"])
    if "contactId" in row:
        values.append(row["contactId"])
    identifiers = []
    for value in values:
        if value is None or value == "":
            unknown = "missing"
            continue
        try:
            identifiers.append(selection_id(value))
        except CalculationError:
            unknown = "invalid"
    if len(set(identifiers)) > 1:
        return {"state": "conflicting"}
    if unknown or not identifiers:
        return {"state": unknown or "missing"}
    return {"state": "known", "id": identifiers[0]}


def timestamp_evidence(value, timezone):
    """Keep source events separate; optional unknown timing never invents dates."""
    if value is None or value == "":
        return {"state": "missing"}
    try:
        if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            return {"state": "date_only", "source_date": date.fromisoformat(value).isoformat()}
        instant = source_timestamp(value)
        local = instant.astimezone(ZoneInfo(timezone))
        return {"state": "aware", "source": value,
                "utc": instant.astimezone(datetime_timezone.utc).isoformat(),
                "local": local.isoformat(), "local_date": local.date().isoformat()}
    except (ValueError, TypeError, OverflowError, ZoneInfoNotFoundError):
        return {"state": "invalid"}


def _evidence_id_key(value):
    try:
        return (0, selection_id(value), type(value).__name__)
    except CalculationError:
        return (1, type(value).__name__, str(value))


def add_record_evidence(result, candidates, timezone, question_id=None):
    """Private evidence for the exact calculation cohort, not additional history.

    Contact counts use final metric-selected records. Candidate evidence can
    additionally contain excluded older winners or ineligible numeric answers.
    sendAt records sending; endedAt alone never proves a completed response.
    """
    metric = result["metric"]
    selected = set(result["cohort_source_ids"] if metric == "response-rate" else result["source_ids"])
    observed_completed = set(result.get("completed_source_ids", []))
    winners = {group["contact_id"]: group["selected_source_id"]
               for group in result.get("selection_group_counts", [])}
    records, groups, unknown, conflicting, eligible_ratings = [], {}, 0, 0, 0
    for row in sorted(candidates, key=lambda item: _evidence_id_key(item["id"])):
        identity = contact_identity(row)
        is_selected = row["id"] in selected
        completed = str(row.get("status", "")).lower() == "completed"
        record = {"survey_id": row["id"], "contact": identity, "status": row.get("status"),
                  "isImported": row.get("isImported") if type(row.get("isImported")) is bool else None,
                  "import_eligible": True, "selected_for_metric": is_selected,
                  "sendAt": timestamp_evidence(row.get("sendAt"), timezone),
                  "endedAt": timestamp_evidence(row.get("endedAt"), timezone)}
        if completed and record["endedAt"]["state"] == "aware":
            record["completed_local_date"] = record["endedAt"]["local_date"]
        if metric == "response-rate":
            record["completed_in_observation"] = row["id"] in observed_completed
        if metric == "nps":
            questions = row.get("questions")
            answers = [item for item in questions if isinstance(item, dict)
                       and str(item.get("questionId")) == str(question_id)] if isinstance(questions, list) else []
            rating = None
            if len(answers) == 1 and answers[0].get("ratingScale") == "0-10":
                try:
                    rating = numeric_rating(answers[0].get("rating"))
                except (TypeError, ValueError, OverflowError):
                    pass
            record.update(question_id=question_id, rating=rating, rating_eligible=rating is not None,
                          rating_category=None if rating is None else "promoter" if rating >= 9 else "passive" if rating >= 7 else "detractor")
            eligible_ratings += rating is not None
        if winners:
            winner = winners.get(identity.get("id"))
            record.update(selected_contact_winner_id=winner,
                          selected_for_contact=row["id"] == winner,
                          excluded_by_latest=row["id"] != winner)
        records.append(record)
        if not is_selected:
            continue
        if identity["state"] == "known":
            group = groups.setdefault(identity["id"], {"contact_id": identity["id"], "survey_ids": [],
                                                      "record_count": 0, "completed_record_count": 0})
            group["survey_ids"].append(row["id"])
            group["record_count"] += 1
            group["completed_record_count"] += completed
        elif identity["state"] == "conflicting":
            conflicting += 1
        else:
            unknown += 1
    summary = {"cohort_basis": "Final records selected for this metric; response-rate counts use its sent denominator cohort",
               "candidate_record_count": len(candidates), "selected_record_count": len(selected),
               "known_contact_record_count": sum(group["record_count"] for group in groups.values()),
               "distinct_known_contact_count": len(groups), "unknown_contact_record_count": unknown,
               "conflicting_contact_record_count": conflicting,
               "identity_complete": unknown == 0 and conflicting == 0,
               "repeated_contact_groups": [group for _, group in sorted(groups.items()) if group["record_count"] > 1]}
    if metric == "nps":
        summary["candidate_records_with_eligible_rating"] = eligible_ratings
    if metric == "response-rate":
        summary["completed_in_observation_count"] = len(observed_completed)
    result.update(contact_summary=summary, record_evidence=records)
    return result


def calculate(rows, metric="nps", question_id=None, since=None, until=None,
              timezone="America/New_York", complete=False, exclude_imported=True,
              observation="period-end", denominator="sent-status", observed_as_of=None,
              latest_in_period=False):
    if type(exclude_imported) is not bool:
        raise CalculationError("Imported-survey policy must be explicit boolean metadata.")
    if type(latest_in_period) is not bool or (latest_in_period and metric not in ("nps", "count")):
        raise CalculationError("Latest-in-period selection is an explicit boolean option for NPS or completed count only.")
    if observation not in ("period-end", "current") or denominator not in ("sent-status", "attempted"):
        raise CalculationError("Unsupported response-rate observation or denominator.")
    if metric != "response-rate" and (observation != "period-end" or denominator != "sent-status" or observed_as_of is not None):
        raise CalculationError("Response-rate options apply only to response-rate calculations.")
    if observed_as_of is not None:
        if not isinstance(observed_as_of, str) or "T" not in observed_as_of or len(observed_as_of) > 80:
            raise CalculationError("Observation time requires an explicit timestamp and timezone.")
        local_day(observed_as_of, timezone)
    if not isinstance(rows, list) or len(rows) > 10000 or metric not in ("nps", "response-rate", "count"):
        raise CalculationError("Unsupported calculation or excessive input.")
    try:
        lower, upper = date.fromisoformat(since), date.fromisoformat(until)
        ZoneInfo(timezone)
    except (ValueError, TypeError, ZoneInfoNotFoundError):
        raise CalculationError("Calculation requires exact dates and an IANA timezone.") from None
    if upper < lower:
        raise CalculationError("Calculation period ends before it starts.")
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or None in ids:
        raise CalculationError("Survey records require unique stable source IDs.")
    identity_keys = [selection_id(value) for value in ids] if latest_in_period else ids
    if len(set(identity_keys)) != len(ids):
        raise CalculationError("Survey records require unique stable source IDs.")
    def in_period(value):
        day = local_day(value, timezone)
        return day is not None and lower <= day <= upper
    policy = "exclude imported surveys" if exclude_imported else "include imported surveys"
    base = {"import_policy": policy, "metric": metric, "since": since, "until": until, "timezone": timezone,
            "input_complete": complete is True, "retrieved_rows": len(rows),
            "coverage_basis": "Selected retrieved records; completeness applies only to their source queries."}
    def apply_import_policy(selected):
        unknown = sum(type(row.get("isImported")) is not bool for row in selected)
        if exclude_imported and unknown:
            raise CalculationError("Selected surveys need explicit boolean isImported values to exclude imported responses. Supply that field or explicitly include all selected surveys.")
        base["import_status_unknown_count"] = unknown
        if unknown:
            base["import_policy"] = "include all selected surveys; import status is unknown for some records"
        return [row for row in selected if not exclude_imported or row["isImported"] is False]
    if metric == "response-rate":
        sent_statuses = ("in-progress", "completed", "abandoned", "no-response")
        selected, unknown_cohort = [], 0
        for row in rows:
            status = str(row.get("status", "")).lower().replace(" ", "-")
            if status == "scheduled":
                continue
            if not row.get("sendAt"):
                unknown_cohort += 1
                continue
            if not in_period(row["sendAt"]):
                continue
            if status not in sent_statuses:
                unknown_cohort += 1
                continue
            selected.append(row)
        if unknown_cohort and (observation != "period-end" or denominator != "sent-status"):
            raise CalculationError("Response-rate cohort has missing status or send-date coverage.")
        cohort = apply_import_policy(selected)
        evidence_rows = list(cohort)
        no_attempt_ids = []
        if denominator == "attempted":
            eligible = []
            for row in cohort:
                attempts = row.get("attempts")
                if not isinstance(attempts, list) or len(attempts) > 1000:
                    raise CalculationError("Attempted response rate requires a bounded explicit attempts array for every selected survey; missing coverage is unknown, not zero attempts.")
                qualifies = False
                for attempt in attempts:
                    if (not isinstance(attempt, dict) or "type" not in attempt or "createdAt" not in attempt
                            or (attempt["type"] is not None and (not isinstance(attempt["type"], str) or len(attempt["type"]) > 100))
                            or not isinstance(attempt["createdAt"], str) or "T" not in attempt["createdAt"] or len(attempt["createdAt"]) > 80):
                        raise CalculationError("Attempt records require a nullable type and an explicit timestamp.")
                    attempt_day = local_day(attempt["createdAt"], timezone)
                    qualifies = qualifies or observation == "current" or attempt_day <= upper
                if qualifies:
                    eligible.append(row)
                else:
                    no_attempt_ids.append(row["id"])
            cohort = eligible
        completed, missing_end_ids = [], []
        for row in cohort:
            if str(row.get("status", "")).lower() != "completed":
                continue
            if not row.get("endedAt"):
                missing_end_ids.append(row["id"])
                if observation == "current":
                    completed.append(row)
                continue
            ended_day = local_day(row["endedAt"], timezone)
            if observation == "current" or ended_day <= upper:
                completed.append(row)
        base.update(sent_count=len(cohort), cohort_completed_count=len(completed),
                    response_rate=100 * len(completed) / len(cohort) if cohort else None,
                    cohort_source_ids=sorted(r["id"] for r in cohort),
                    completed_source_ids=sorted(r["id"] for r in completed),
                    observation=observation, observed_as_of=observed_as_of,
                    observation_cutoff=until if observation == "period-end" else None,
                    status_basis="Current status in supplied records; historical status transitions are not reconstructed",
                    denominator=denominator,
                    attempt_basis="Presence of an outreach-attempt record; not proof of delivery" if denominator == "attempted" else None,
                    attempt_observation_cutoff=until if denominator == "attempted" and observation == "period-end" else None,
                    excluded_no_attempt_count=len(no_attempt_ids), excluded_no_attempt_source_ids=sorted(no_attempt_ids),
                    attempt_coverage="explicit for selected cohort" if denominator == "attempted" else "not used",
                    cohort_fields_unknown_count=unknown_cohort,
                    completion_date_unknown_count=len(missing_end_ids),
                    observation_complete=not unknown_cohort and (observation == "current" or not missing_end_ids))
        return add_record_evidence(base, evidence_rows, timezone)
    candidates = [row for row in rows if str(row.get("status", "")).lower() == "completed"]
    if latest_in_period:
        for row in rows:
            if exclude_imported and row.get("isImported") is True:
                continue
            status = str(row.get("status", "")).lower().replace(" ", "-")
            if status not in ("completed", "scheduled", "in-progress", "abandoned", "no-response"):
                if not row.get("endedAt") or in_period(row["endedAt"]):
                    raise CalculationError("Latest-in-period selection needs known lifecycle status for potentially relevant records.")
        candidates = [row for row in candidates if not (exclude_imported and row.get("isImported") is True)]
        if any(not row.get("endedAt") for row in candidates):
            raise CalculationError("Latest-in-period selection cannot establish the period without completion timestamps.")
    completed = apply_import_policy([row for row in candidates if in_period(row.get("endedAt"))])
    evidence_rows = list(completed)
    if latest_in_period:
        completed, selection = latest_completed_per_contact(completed, complete)
        base.update(selection)
    source_id_key = selection_id if latest_in_period else None
    if metric == "count":
        base.update(completed_count=len(completed), source_ids=sorted((r["id"] for r in completed), key=source_id_key))
        return add_record_evidence(base, evidence_rows, timezone)
    if question_id is None:
        raise CalculationError("NPS requires the verified recommendation question ID.")
    values = []
    for row in completed:
        answers = [q for q in row.get("questions", []) if str(q.get("questionId")) == str(question_id)]
        if len(answers) != 1 or answers[0].get("ratingScale") != "0-10":
            continue
        rating = numeric_rating(answers[0].get("rating"))
        if rating is not None:
            values.append((row["id"], rating))
    promoters = sum(v >= 9 for _, v in values)
    detractors = sum(v <= 6 for _, v in values)
    n = len(values)
    exact_score = Fraction(100 * (promoters - detractors), n) if n else None
    base.update(nps=100 * (promoters - detractors) / len(values) if values else None,
                nps_calculation=f"100 * ({promoters} - {detractors}) / {n} = {exact_score}" if n else None,
                n=len(values), promoters=promoters, passives=len(values)-promoters-detractors,
                detractors=detractors, source_ids=sorted((i for i, _ in values), key=source_id_key),
                excluded_completed_count=len(completed)-len(values),
                question_id=question_id)
    return add_record_evidence(base, evidence_rows, timezone, question_id)



SNAPSHOT_MAX_BYTES = 16_000_000
SNAPSHOT_MAX_RECORDS = 10_000
SNAPSHOT_MAX_GROUPS = 200
SNAPSHOT_MAX_SCENARIOS = 50


def _snapshot_text(value, limit, diagnostic):
    if type(value) is not str or not value.strip() or len(value) > limit:
        raise CalculationError(diagnostic)
    return value


def _snapshot_id(value):
    if type(value) is int and 0 <= value <= 2**63 - 1:
        return (int, value)
    if (type(value) is str and value and value == value.strip() and len(value) <= 256
            and all(ord(c) >= 32 for c in value)):
        return (str, value)
    raise CalculationError("Snapshot records and scenarios need stable string or nonnegative integer source IDs.")


def _snapshot_rating(value):
    if type(value) is not int or not 0 <= value <= 10:
        raise CalculationError("Snapshot ratings must be integer numbers from 0 through 10.")
    return value


def _snapshot_summary(rows, include_ids=True):
    n = len(rows)
    promoters = sum(row["rating"] >= 9 for row in rows)
    passives = sum(7 <= row["rating"] <= 8 for row in rows)
    detractors = sum(row["rating"] <= 6 for row in rows)
    if promoters + passives + detractors != n:
        raise CalculationError("Snapshot category counts do not reconcile to the selected cohort.")
    exact_score = Fraction(100 * (promoters - detractors), n) if n else None
    result = {"n": n, "promoters": promoters, "passives": passives, "detractors": detractors,
              "nps": 100 * (promoters - detractors) / n if n else None,
              "nps_calculation": f"100 * ({promoters} - {detractors}) / {n} = {exact_score}" if n else None}
    if include_ids:
        result["source_ids"] = [row["id"] for row in rows]
    return result


def calculate_snapshot(payload, group_by=None):
    """NPS for an explicitly supplied cohort; no dates or live/API policies inferred."""
    if (type(payload) is not dict or not {"cohort", "recommendation", "responses"} <= set(payload)
            or set(payload) - {"cohort", "recommendation", "responses", "scenarios"}):
        raise CalculationError("Snapshot needs only cohort, recommendation, responses and optional requested scenarios.")
    cohort = _snapshot_text(payload["cohort"], 1000, "Snapshot needs an explicit supplied-cohort description.")
    recommendation = payload["recommendation"]
    if (type(recommendation) is not dict or set(recommendation) != {"verified", "scale", "basis"}
            or recommendation["verified"] is not True or recommendation["scale"] != "0-10"):
        raise CalculationError("Snapshot NPS requires a verified genuine 0-10 recommendation definition and its source basis.")
    _snapshot_text(recommendation["basis"], 2000, "Snapshot recommendation definition needs a nonempty source basis.")
    rows = payload["responses"]
    if type(rows) is not list or len(rows) > SNAPSHOT_MAX_RECORDS:
        raise CalculationError("Snapshot responses must be a list of at most 10000 records.")
    if group_by is not None and (type(group_by) is not str or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,63}", group_by)):
        raise CalculationError("Snapshot grouping requires one actual bounded field name.")
    by_id, seen_ids, groups = {}, set(), {}
    for row in rows:
        if type(row) is not dict or "id" not in row or "rating" not in row:
            raise CalculationError("Every snapshot response needs its actual source id and rating.")
        identity = _snapshot_id(row["id"])
        # Mixed 1 / "1" IDs are ambiguous source identities, not two new responses.
        normalized = str(row["id"])
        if normalized in seen_ids:
            raise CalculationError("Snapshot response IDs must be unique and unambiguous.")
        seen_ids.add(normalized)
        _snapshot_rating(row["rating"])
        by_id[identity] = row
        if group_by is not None:
            value = row.get(group_by)
            if type(value) is str:
                _snapshot_text(value, 256, "Every snapshot response needs an actual bounded group value.")
            elif type(value) is not int or not -(2**63) <= value <= 2**63 - 1:
                raise CalculationError("Snapshot group values must be observed nonempty strings or bounded integers.")
            groups.setdefault((type(value), value), []).append(row)
            if len(groups) > SNAPSHOT_MAX_GROUPS:
                raise CalculationError("Snapshot grouping exceeds the 200-group budget.")
    scenarios = payload.get("scenarios", [])
    if type(scenarios) is not list or len(scenarios) > SNAPSHOT_MAX_SCENARIOS:
        raise CalculationError("Snapshot supports at most 50 explicitly requested one-record scenarios.")
    labels, checked_scenarios = set(), []
    for scenario in scenarios:
        if type(scenario) is not dict or set(scenario) != {"label", "response_id", "new_rating"}:
            raise CalculationError("Each requested snapshot scenario needs label, response_id and new_rating only.")
        label = _snapshot_text(scenario["label"], 200, "Snapshot scenarios need bounded nonempty labels.")
        if label in labels:
            raise CalculationError("Snapshot scenario labels must be unique.")
        labels.add(label)
        identity = _snapshot_id(scenario["response_id"])
        if identity not in by_id:
            raise CalculationError("Snapshot scenario target must match an actual source ID and its type.")
        checked_scenarios.append((label, by_id[identity], _snapshot_rating(scenario["new_rating"])))
    baseline = _snapshot_summary(rows)
    result = {"metric": "snapshot-nps", "source_kind": "supplied snapshot; not a live API retrieval",
              "cohort": cohort, "recommendation": dict(recommendation),
              "selection_policy": "All provided responses in the explicitly declared supplied cohort; no API lifecycle, date or import policy is inferred.",
              "baseline": baseline}
    if group_by is not None:
        result["group_by"] = group_by
        result["groups"] = [{"group_value": value, **_snapshot_summary(members)}
                            for (_, value), members in groups.items()]
    if checked_scenarios:
        result["scenario_scope"] = "Each requested one-record scenario independently starts from the original baseline cohort and its baseline.source_ids."
        result["scenarios"] = []
        baseline_counts = _snapshot_summary(rows, include_ids=False)
        for label, original, new_rating in checked_scenarios:
            changed = [dict(row, rating=new_rating) if row is original else row for row in rows]
            outcome = _snapshot_summary(changed, include_ids=False)
            if outcome["n"] != baseline["n"]:
                raise CalculationError("Snapshot scenario changed the fixed denominator.")
            delta = 100 * ((outcome["promoters"] - outcome["detractors"])
                           - (baseline["promoters"] - baseline["detractors"])) / baseline["n"]
            result["scenarios"].append({"label": label, "response_id": original["id"],
                                        "original_rating": original["rating"], "new_rating": new_rating,
                                        "baseline": dict(baseline_counts), "result": outcome,
                                        "delta_nps": delta, "changed_source_ids": [original["id"]]})
    return result


def _snapshot_json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CalculationError("Snapshot JSON must not contain duplicate object keys.")
        result[key] = value
    return result


def _snapshot_json_constant(value):
    raise CalculationError("Snapshot JSON must not contain non-finite numbers.")


def _snapshot_display_number(value, signed=False):
    text = f"{value:.1f}".rstrip("0").rstrip(".") if value else "0"
    return "+" + text if signed and value > 0 else text


def _snapshot_display_cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def calendar_period(reference_date, relative):
    """Resolve a full local calendar month from an explicit date; never read a clock."""
    if not isinstance(reference_date, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", reference_date):
        raise CalculationError("Reference date must be an exact valid YYYY-MM-DD local calendar date.")
    try:
        reference = date.fromisoformat(reference_date)
    except ValueError:
        raise CalculationError("Reference date must be an exact valid YYYY-MM-DD local calendar date.") from None
    offsets = {"previous-month": -1, "current-month": 0, "next-month": 1}
    if not isinstance(relative, str) or relative not in offsets:
        raise CalculationError("Relative period must be previous-month, current-month or next-month.")
    year, month_index = divmod(reference.year * 12 + reference.month - 1 + offsets[relative], 12)
    if not 1 <= year <= 9999:
        raise CalculationError("Requested calendar month is outside supported years 0001 through 9999.")
    month = month_index + 1
    first = date(year, month, 1)
    last = date(year, month, monthrange(year, month)[1])
    return {"reference_date": reference.isoformat(), "relative": relative,
            "period": f"{year:04d}-{month:02d}", "period_label": f"{MONTH_NAMES[month - 1]} {year}",
            "since": first.isoformat(), "until": last.isoformat()}


def business_period(since, until):
    first, last = date.fromisoformat(since), date.fromisoformat(until)
    start = f"{MONTH_NAMES[first.month - 1]} {first.day}"
    if first == last:
        return start + f", {first.year}"
    if first.year == last.year and first.month == last.month:
        return start + f"–{last.day}, {last.year}"
    if first.year == last.year:
        return start + f"–{MONTH_NAMES[last.month - 1]} {last.day}, {last.year}"
    return start + f", {first.year}–{MONTH_NAMES[last.month - 1]} {last.day}, {last.year}"


def business_month(value):
    parsed = date.fromisoformat(value + "-01")
    return f"{MONTH_NAMES[parsed.month - 1]} {parsed.year}"


def _business_month_gap(rows):
    numbers = [int(row["period"][:4]) * 12 + int(row["period"][5:]) for row in rows]
    return any(right - left != 1 for left, right in zip(numbers, numbers[1:]))


def _business_score_pattern(rows):
    available = [row for row in rows if row["nps"] is not None]
    if not available:
        return "No month shown has a recommendation score."
    if len(available) < len(rows) or _business_month_gap(rows):
        return "Not every month has a score, so these figures do not show an uninterrupted monthly trend."
    scores = [round(row["nps"], 1) for row in available]
    if len(scores) < 2:
        return ""
    changes = [right - left for left, right in zip(scores, scores[1:])]
    if all(change == 0 for change in changes):
        return "The scores stayed at about the same level."
    if all(change >= 0 for change in changes):
        return "The score increased across the months shown."
    if all(change <= 0 for change in changes):
        return "The score decreased across the months shown."
    if len(scores) == 3 and scores[1] < scores[0] and scores[2] > scores[1]:
        ending = "partly recovered, finishing below the first month's level" if scores[2] < scores[0] else "recovered to its starting level" if scores[2] == scores[0] else "rose above its starting level"
        return "The score fell, then " + ending + "."
    if len(scores) == 3 and scores[1] > scores[0] and scores[2] < scores[1]:
        ending = "above" if scores[2] > scores[0] else "below" if scores[2] < scores[0] else "at"
        return "The score rose, then fell, finishing " + ending + " its starting level."
    return "The score moved up and down across the months shown."


def business_recommendation_readout(score, responses, *, period=None, people=None, monthly=None, groups=None, selection_note=None):
    """Render verified metric results; sample wording is a display cue, not a validity threshold."""
    when = " for " + period if period else ""
    if score is None:
        return "No recommendation score is available" + when + ": there were no valid recommendation ratings."
    sample = f"{responses} survey {'response' if responses == 1 else 'responses'}"
    if type(people) is int and 0 < people <= responses:
        sample += f" from {people} {'person' if people == 1 else 'people'}"
    text = f"Your recommendation score (NPS){when} was {_snapshot_display_number(score)}, based on {sample}."
    if selection_note:
        text += "\n\n" + selection_note
    rows = monthly or []
    if rows:
        lines = ["Month | NPS | Responses | Change", "--- | --- | --- | ---"]
        previous = None
        for row in rows:
            value = row["nps"]
            change = "—" if previous is None or value is None else _snapshot_display_number(value - previous, signed=True) + " points"
            shown = "Not available" if value is None else _snapshot_display_number(value)
            lines.append(f"{business_month(row['period'])} | {shown} | {row['responses']} | {change}")
            previous = value
        text += "\n\n" + "\n".join(lines)
        pattern = _business_score_pattern(rows)
        if pattern:
            text += "\n\n" + pattern
        counts = [row["responses"] for row in rows if row["nps"] is not None and row["responses"] > 0]
        # This never suppresses a score or asserts a minimum required sample.
        if counts and max(counts) <= 10:
            low, high = min(counts), max(counts)
            sample_size = str(low) if low == high else f"{low}–{high}"
            unit = "response" if low == high == 1 else "responses"
            text += f" With only {sample_size} {unit} behind each monthly score, treat these as early signals until more feedback is available."
    elif groups:
        lines = ["Group | NPS | Responses", "--- | --- | ---"]
        lines += [f"{_snapshot_display_cell(row['group_value'])} | {_snapshot_display_number(row['nps'])} | {row['n']}" for row in groups]
        text += "\n\n" + "\n".join(lines)
    elif 0 < responses <= 10:
        text += "\n\nThis is a small set of responses, so treat the score as an early signal and see whether it holds as more feedback comes in."
    return text


def snapshot_source_readout(result):
    n = result["baseline"]["n"]
    text = f"I used the {n} recommendation {'rating' if n == 1 else 'ratings'} in the feedback you provided."
    if result.get("group_by") == "month":
        text += " The monthly breakdown follows the month labels in that feedback."
    elif result.get("groups"):
        text += " The breakdown follows the groups in that feedback."
    return text


def snapshot_readout(result):
    """Business display of computed snapshot results, without changing arithmetic."""
    groups = result.get("groups", [])
    chronological = result.get("group_by") == "month" and bool(groups)
    if chronological:
        try:
            chronological = all(isinstance(group["group_value"], str)
                and re.fullmatch(r"[0-9]{4}-[0-9]{2}", group["group_value"])
                and date.fromisoformat(group["group_value"] + "-01") for group in groups)
        except (ValueError, TypeError):
            chronological = False
    monthly = None
    if chronological:
        monthly = [{"period": group["group_value"], "nps": group["nps"], "responses": group["n"]}
                   for group in sorted(groups, key=lambda group: group["group_value"])]
    text = business_recommendation_readout(result["baseline"]["nps"], result["baseline"]["n"],
                                            monthly=monthly, groups=groups if not chronological else None)
    if result.get("scenarios"):
        lines = ["Requested change | NPS | Change from original score", "--- | --- | ---"]
        for scenario in result["scenarios"]:
            lines.append(f"{_snapshot_display_cell(scenario['label'])} | "
                         f"{_snapshot_display_number(scenario['result']['nps'])} | "
                         f"{_snapshot_display_number(scenario['delta_nps'], signed=True)} points")
        text += "\n\n" + "\n".join(lines)
    return text


def _evidence_label(value):
    value = _snapshot_text(value, 200, "Evidence labels must be nonempty bounded text.")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise CalculationError("Evidence labels must not contain control characters.")
    return value


def _evidence_day(value):
    if type(value) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    raise CalculationError("Date filters require exact valid YYYY-MM-DD values.")


def _evidence_number(value):
    # JSON callbacks retain the original token; Python floats are already lossy.
    if type(value) not in (str, int, Decimal):
        raise CalculationError("Numeric filters require exact bounded decimal values, not floats.")
    try:
        text = str(value)
        if len(text) > 64 or not re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", text):
            raise ValueError()
        exponent = re.search(r"[eE]([+-]?[0-9]+)$", text)
        if exponent and abs(int(exponent.group(1))) > 1000:
            raise ValueError()
        number = Decimal(text)
        if not number.is_finite() or not -1000 <= number.as_tuple().exponent <= 1000:
            raise ValueError()
        return number
    except (ValueError, OverflowError, InvalidOperation):
        raise CalculationError("Numeric filters require valid finite decimal tokens of at most 64 characters and exponent magnitude at most 1000.") from None


def count_csv_evidence(raw, spec):
    """Check supplied memberships against actual CSV rows; never classify meaning."""
    if type(raw) is not bytes or len(raw) > SNAPSHOT_MAX_BYTES:
        raise CalculationError("CSV input must be bounded UTF-8 bytes.")
    if type(spec) is not dict or not {"fields", "scope", "themes"} <= set(spec) or set(spec) - {"fields", "scope", "themes", "rating_association", "recommendation", "record_unit", "group_by"}:
        raise CalculationError("Evidence spec requires explicit fields, scope and themes; unknown fields are refused.")
    unit = spec.get("record_unit", "responses")
    if type(unit) is not str or unit not in ("responses", "reviews"):
        raise CalculationError("record_unit must be responses or reviews; source kind is caller-verified.")
    fields = spec["fields"]
    if type(fields) is not dict or not {"id", "text"} <= set(fields) or set(fields) - {"id", "text", "rating"} or any(type(v) is not str or not v or len(v) > 256 for v in fields.values()) or len(set(fields.values())) != len(fields):
        raise CalculationError("Map distinct id and text CSV columns explicitly; rating is optional without association.")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        header = reader.fieldnames
        if not header or len(header) > 100 or len(set(header)) != len(header) or any(not v for v in header) or not set(fields.values()) <= set(header):
            raise CalculationError("CSV needs unique nonblank headers and the exact mapped columns.")
        rows, by_id = [], {}
        for row in reader:
            if len(rows) >= SNAPSHOT_MAX_RECORDS or set(row) != set(header) or any(v is None for v in row.values()):
                raise CalculationError("CSV row budget exceeded or row columns do not match the header.")
            identifier = row[fields["id"]]
            _snapshot_id(identifier)
            if identifier in by_id:
                raise CalculationError("CSV source IDs must be unique; no automatic deduplication.")
            rows.append(row)
            by_id[identifier] = row
    except (UnicodeError, csv.Error):
        raise CalculationError("CSV must contain valid bounded UTF-8 records.") from None
    scope = spec["scope"]
    if type(scope) is not dict or not {"label"} <= set(scope) or set(scope) - {"label", "filters"}:
        raise CalculationError("Scope needs a label and optional explicit filters, never a declared count.")
    scope_label = _evidence_label(scope["label"])
    filters = scope.get("filters", [])
    if type(filters) is not list or len(filters) > 8:
        raise CalculationError("Evidence scope supports at most eight AND filters.")
    compiled = []
    for item in filters:
        if type(item) is not dict or item.get("field") not in header:
            raise CalculationError("Every filter must name an actual CSV field.")
        op = item.get("op")
        if op == "eq" and set(item) == {"field", "op", "value"} and type(item["value"]) is str and len(item["value"]) <= 256:
            bounds = (item["value"],)
        elif op == "date-range" and set(item) == {"field", "op", "since", "until"}:
            bounds = (_evidence_day(item["since"]), _evidence_day(item["until"]))
        elif op == "numeric-range" and set(item) == {"field", "op", "minimum", "maximum"} and all(type(item[k]) in (int, Decimal) for k in ("minimum", "maximum")):
            bounds = (_evidence_number(item["minimum"]), _evidence_number(item["maximum"]))
        else:
            raise CalculationError("Use exact eq, inclusive date-range or inclusive numeric-range filters.")
        if len(bounds) == 2 and bounds[0] > bounds[1]:
            raise CalculationError("Filter lower bound must not exceed its upper bound.")
        compiled.append((item["field"], op, bounds))
    selected = []
    for row in rows:
        keep = True
        for field, op, bounds in compiled:
            value = row[field]
            if op == "date-range":
                value = _evidence_day(value)
            elif op == "numeric-range":
                value = _evidence_number(value)
            if not (value == bounds[0] if op == "eq" else bounds[0] <= value <= bounds[1]):
                keep = False
                break
        if keep:
            selected.append(row[fields["id"]])
    selected_ids = set(selected)
    group_by, observed_groups = spec.get("group_by"), set()
    if "group_by" in spec:
        if type(group_by) is not str or group_by not in header:
            raise CalculationError("group_by must name one actual CSV column.")
        for identifier in selected:
            value = _evidence_label(by_id[identifier][group_by])
            observed_groups.add(value)
            if len(observed_groups) > SNAPSHOT_MAX_GROUPS:
                raise CalculationError(f"Grouping supports at most {SNAPSHOT_MAX_GROUPS} observed values in the selected rows.")
    association = spec.get("rating_association", False)
    if type(association) is not bool:
        raise CalculationError("rating_association must be an explicit boolean.")
    if association:
        if "rating" not in fields:
            raise CalculationError("Rating association requires an explicit actual rating column.")
        recommendation = spec.get("recommendation")
        if type(recommendation) is not dict or set(recommendation) != {"verified", "scale", "basis"} or recommendation["verified"] is not True or recommendation["scale"] != "0-10":
            raise CalculationError("Rating association requires a verified 0-10 recommendation definition.")
        _snapshot_text(recommendation["basis"], 1000, "Record the supplied recommendation meaning.")
    themes = spec["themes"]
    if type(themes) is not list or not 1 <= len(themes) <= SNAPSHOT_MAX_SCENARIOS:
        raise CalculationError("Supply between one and fifty evidence themes.")
    output, labels = [], set()
    for theme in themes:
        if type(theme) is not dict or set(theme) != {"label", "evidence"}:
            raise CalculationError("Each theme needs its unchanged label and evidence, never a declared count.")
        label = _evidence_label(theme["label"])
        if label in labels:
            raise CalculationError("Theme labels must be unique.")
        labels.add(label)
        members = theme["evidence"]
        if type(members) is not list or len(members) > SNAPSHOT_MAX_RECORDS:
            raise CalculationError("Theme evidence must be a bounded list of source IDs and exact quotes.")
        identifiers, checked, low = set(), [], 0
        for member in members:
            if type(member) is not dict or set(member) != {"id", "quote"} or type(member["id"]) is not str:
                raise CalculationError("Evidence needs a CSV string source ID and an exact quote.")
            identifier = member["id"]
            if identifier in identifiers or identifier not in by_id:
                raise CalculationError("Theme evidence contains duplicate or unknown source IDs.")
            if identifier not in selected_ids:
                raise CalculationError("Theme evidence contains a source ID outside the computed scope.")
            text, quote = by_id[identifier][fields["text"]], member["quote"]
            _snapshot_text(quote, 20_000, "Evidence quotes must be nonblank bounded source text.")
            if not text.strip() or quote not in text:
                raise CalculationError("Every exact quote must occur in its own nonblank source comment.")
            identifiers.add(identifier)
            checked.append({"id": identifier, "quote": quote})
            if association:
                rating = numeric_rating(by_id[identifier][fields["rating"]])
                if rating is None:
                    raise CalculationError("Rating association requires valid integer 0-10 ratings on every theme response.")
                low += rating <= 6
        count = len(identifiers)
        result = {"label": label, "record_count": count, "response_count": count, "denominator": len(selected),
                  "readout": f'{count} of {len(selected)} {unit} mention “{label}”.' if selected else f"No {unit} are available for this selection.", "evidence": checked}
        if group_by is not None:
            matched = {}
            for member in checked:
                value = by_id[member["id"]][group_by]
                matched.setdefault(value, []).append(member["id"])
            groups = [{"value": value, "record_count": len(matched[value]),
                       "source_ids": sorted(matched[value])} for value in sorted(matched)]
            names = [f'“{group["value"]}”' for group in groups]
            names = ", ".join(names[:-1]) + f", and {names[-1]}" if len(names) > 2 else " and ".join(names)
            group_readout = (f'{unit.capitalize()} mentioning “{label}” came from {names}.' if groups else
                             f'No supporting {unit} were supplied for “{label}”.' if selected else
                             f"No {unit} are available for this selection.")
            result["grouping"] = {"matched_group_count": len(groups), "groups": groups, "readout": group_readout}
        if association:
            result["rating_association"] = {"low_score_response_count": low, "rated_response_count": count,
                "readout": f'{low} of {count} {unit} mentioning “{label}” were rated 0–6.' if count else f'No {unit[:-1]} evidence was supplied for “{label}”.'}
        output.append(result)
    result = {"state": "checked", "count_unit": unit,
            "record_unit_basis": "Caller declaration or responses default; source kind is not inferred or verified.",
            "source_record_count": len(rows), "scope_record_count": len(selected),
            "verification_scope": {"membership_only": True, "semantic_classification": False,
                                   "exhaustive_classification": False, "business_source_complete": False},
            "source_csv_sha256": hashlib.sha256(raw).hexdigest(), "source_response_count": len(rows),
            "scope_label": scope_label, "scope_response_count": len(selected), "scope_source_ids": selected,
            "classification_basis": "Supplied memberships checked against source IDs, scope and exact quotes; theme meaning and exhaustiveness are not verified.",
            "themes": output}
    if group_by is not None:
        result["grouping"] = {"field": group_by, "observed_group_count": len(observed_groups),
                              "observed_groups": sorted(observed_groups),
                              "basis": "Observed values in selected source rows; business roles and hierarchy are not verified."}
    return result


REPORTING_INDEX_NAMES = {1: "4 stars or better", 2: "5 stars", 3: "3 stars or better",
                         4: "2 stars or better", 5: "Net Promoter Score (NPS)", 6: "Average rating"}
REPORTING_STAR_MAP = (1, 1, 2, 2, 3, 3, 3, 4, 4, 5, 5)


def _index_round(value, places=0):
    """PHP ROUND_HALF_UP, including negative ties; arithmetic stays exact until display."""
    factor = 10 ** places
    magnitude = (abs(value.numerator) * factor * 2 + value.denominator) // (2 * value.denominator)
    rounded = magnitude if value >= 0 else -magnitude
    return rounded if not places else rounded / factor


def _index_proof(value, allowed, required):
    if type(value) is not dict or set(value) - allowed or not required <= set(value):
        raise CalculationError("Reporting context has missing or unsupported fields.")
    if type(value["verified"]) is not bool:
        raise CalculationError("Reporting context verification must be a boolean.")
    _snapshot_text(value["basis"], 2000, "Reporting context needs a bounded nonempty source basis.")
    return value["verified"]


def _index_pending(state, readout):
    return {"state": state, "readout": readout}


def calculate_reporting_index(payload, group_by=None):
    """Apply an explicitly verified GQ reporting index to an already selected source cohort.

    Caller evidence establishes preference, scope, question identity and report aggregation.
    This offline calculation neither discovers account preferences nor verifies those declarations.
    """
    allowed = {"scope", "complete", "preferences", "aggregation", "questions", "responses"}
    if (type(payload) is not dict or set(payload) - allowed
            or not {"scope", "complete", "preferences"} <= set(payload)):
        raise CalculationError("Reporting index needs scope, completeness and explicit preference context.")
    scope = _snapshot_text(payload["scope"], 1000, "Reporting index needs an explicit feedback scope.")
    if type(payload["complete"]) is not bool:
        raise CalculationError("Reporting index completeness must be a boolean.")
    prefs = payload["preferences"]
    if type(prefs) is not dict or set(prefs) - {"requested", "report", "company", "report_context", "report_inherits_company"}:
        raise CalculationError("Reporting preferences contain unsupported fields.")
    checked = {}
    for origin in ("requested", "report", "company"):
        pref = prefs.get(origin)
        if pref is None:
            continue
        verified = _index_proof(pref, {"id", "verified", "basis"}, {"id", "verified", "basis"})
        if type(pref["id"]) is not int or pref["id"] not in REPORTING_INDEX_NAMES:
            raise CalculationError("Reporting index must be an integer ID from 1 through 6.")
        checked[origin] = (origin, pref, verified)
    report_context = prefs.get("report_context")
    if report_context is not None and report_context not in ("none", "selected"):
        raise CalculationError("Report context must explicitly be none or selected.")
    inherited = prefs.get("report_inherits_company")
    inherits_verified = False
    if inherited is not None:
        inherits_verified = _index_proof(inherited, {"verified", "basis"}, {"verified", "basis"})
    if report_context == "none" and (prefs.get("report") is not None or inherited is not None):
        raise CalculationError("A report preference requires a selected report context.")
    if prefs.get("report") is not None and inherited is not None:
        raise CalculationError("A report cannot both override and inherit its reporting index.")
    if "requested" in checked:
        selected = checked["requested"]
    elif report_context == "selected":
        selected = checked.get("report") if not inherits_verified else checked.get("company")
    elif report_context == "none":
        selected = checked.get("company")
    else:
        selected = None
    if selected is None or not selected[2]:
        return _index_pending("needs_preference", "Which measure do you use in your report: NPS, average rating, or a percentage of positive ratings?")
    origin, pref, _ = selected
    index_id = pref["id"]
    if not payload["complete"]:
        return _index_pending("incomplete", "I need the rest of the selected feedback before calculating this score.")
    aggregation = payload.get("aggregation")
    if aggregation is None:
        return _index_pending("needs_context", "Does your report give each survey equal weight, or count each question response equally?")
    verified = _index_proof(aggregation, {"mode", "verified", "basis", "question_ids", "survey_values_basis"},
                            {"mode", "verified", "basis"})
    mode = aggregation["mode"]
    if mode not in ("questions", "surveys"):
        raise CalculationError("Reporting aggregation must be questions or surveys.")
    if not verified:
        return _index_pending("needs_context", "Does your report give each survey equal weight, or count each question response equally?")
    selected_questions = None
    if mode == "questions":
        ids = aggregation.get("question_ids")
        if type(ids) is not list or not 1 <= len(ids) <= 200:
            raise CalculationError("Question-based reporting needs its explicit selected question IDs.")
        selected_questions = set()
        for identifier in ids:
            _snapshot_id(identifier)
            key = str(identifier)
            if key in selected_questions:
                raise CalculationError("Selected question IDs must be unique and unambiguous.")
            selected_questions.add(key)
    elif "question_ids" in aggregation:
        raise CalculationError("Survey-based reporting uses all supplied questions, not a guessed question selection.")
    survey_values_basis = aggregation.get("survey_values_basis")
    if survey_values_basis is not None:
        _snapshot_text(survey_values_basis, 2000, "Saved survey averages need a bounded source basis.")
    definitions = payload.get("questions")
    rows = payload.get("responses")
    if type(definitions) is not list or not 1 <= len(definitions) <= 200:
        raise CalculationError("Reporting index needs at most 200 verified source question definitions.")
    questions, canonical = {}, []
    for question in definitions:
        fields = {"id", "scale", "meaning", "direction", "verified", "basis", "canonical_ltr"}
        if not _index_proof(question, fields, fields - {"canonical_ltr"}):
            return _index_pending("needs_context", "I need the question wording and rating scale before calculating this measure.")
        _snapshot_id(question["id"])
        key = str(question["id"])
        if key in questions:
            raise CalculationError("Question definitions must have unique unambiguous source IDs.")
        if (question["scale"] not in ("0-10", "1-5")
                or question["meaning"] not in ("recommendation", "satisfaction", "effort", "rating")
                or question["direction"] not in ("higher", "lower")
                or type(question.get("canonical_ltr", False)) is not bool):
            raise CalculationError("Question meaning, direction or scale is unsupported.")
        if question.get("canonical_ltr"):
            if question["meaning"] != "recommendation" or question["direction"] != "higher":
                raise CalculationError("Canonical LTR must be a verified higher-is-better recommendation question.")
            canonical.append(key)
        questions[key] = question
    if len(canonical) > 1:
        raise CalculationError("GQ reporting needs one unambiguous canonical LTR question.")
    if selected_questions is not None and not selected_questions <= questions.keys():
        raise CalculationError("Every selected question needs a verified source definition.")
    active = selected_questions if selected_questions is not None else set(questions)
    if index_id == 5:
        if not canonical or canonical[0] not in active:
            return _index_pending("unavailable", "NPS isn’t available from these questions. It needs the verified Likely to Recommend question; satisfaction and other ratings cannot replace it.")
        active = {canonical[0]}
    if index_id in (1, 2, 3, 4) and any(questions[key]["direction"] != "higher" for key in active):
        return _index_pending("needs_context", "This question’s lower ratings mean a better experience. Which positive-rating rule does your report use for it?")
    if type(rows) is not list or len(rows) > SNAPSHOT_MAX_RECORDS:
        raise CalculationError("Reporting responses must be a list of at most 10000 surveys.")
    if group_by is not None and (type(group_by) is not str or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,63}", group_by)):
        raise CalculationError("Reporting grouping requires one actual bounded field name.")
    seen, prepared, groups, answer_budget = set(), [], {}, 0
    needs_survey_values = False
    for row in rows:
        if type(row) is not dict or not {"id", "answers"} <= set(row):
            raise CalculationError("Every reporting survey needs its source ID and answers.")
        _snapshot_id(row["id"])
        identity = str(row["id"])
        if identity in seen:
            raise CalculationError("Reporting surveys must have unique unambiguous source IDs.")
        seen.add(identity)
        answers = row["answers"]
        if type(answers) is not list or len(answers) > 200:
            raise CalculationError("Each survey supports at most 200 supplied question answers.")
        answer_budget += len(answers)
        if answer_budget > 100000:
            raise CalculationError("Reporting calculation exceeds its 100000-answer budget.")
        used, ratings = set(), []
        for answer in answers:
            if (type(answer) is not dict or not {"question_id", "rating"} <= set(answer)
                    or set(answer) - {"question_id", "rating", "scale"}):
                raise CalculationError("Each answer needs its source question ID, rating and optional actual source scale.")
            _snapshot_id(answer["question_id"])
            key = str(answer["question_id"])
            if key not in questions or key in used:
                raise CalculationError("Every answer needs a defined, nonduplicated source question ID.")
            used.add(key)
            rating = answer["rating"]
            if rating is None:
                continue
            scale = answer.get("scale", questions[key]["scale"])
            if scale not in ("0-10", "1-5"):
                raise CalculationError("Each supplied source scale must be 0-10 or 1-5.")
            low, high = (0, 10) if scale == "0-10" else (1, 5)
            if type(rating) is not int or not low <= rating <= high:
                raise CalculationError("Ratings must be integer source values within their verified scale, or null for no answer.")
            if key in active:
                ratings.append(REPORTING_STAR_MAP[rating] if low == 0 else rating)
        item = {"id": row["id"], "ratings": ratings}
        if mode == "surveys" and index_id == 6:
            saved = row.get("reporting_value")
            if saved is not None:
                if (type(saved) not in (int, float) or not 1 <= saved <= 5 or not math.isfinite(saved)
                        or survey_values_basis is None):
                    raise CalculationError("Saved survey averages must be verified finite source values from 1 through 5.")
                if len(ratings) == 1 and saved != ratings[0]:
                    raise CalculationError("Saved survey average conflicts with its single source rating.")
                item["reporting_value"] = Fraction(str(saved))
            elif len(ratings) == 1:
                item["reporting_value"] = Fraction(ratings[0])
            elif len(ratings) > 1:
                needs_survey_values = True
        prepared.append(item)
        if group_by is not None:
            value = row.get(group_by)
            _snapshot_id(value)
            group_key = str(value)
            if group_key in groups and groups[group_key]["value"] != value:
                raise CalculationError("Group labels must be unambiguous source values.")
            groups.setdefault(group_key, {"value": value, "rows": []})["rows"].append(item)
            if len(groups) > SNAPSHOT_MAX_GROUPS:
                raise CalculationError("Reporting grouping exceeds the 200-group budget.")

    if needs_survey_values:
        return _index_pending("needs_context", "To match this report’s average rating, please share its saved survey averages or a report export.")

    def summarize(records):
        eligible = [row for row in records if row["ratings"] or "reporting_value" in row]
        ratings = [rating for row in eligible for rating in row["ratings"]]
        answer_count = len(ratings)
        result = {"response_count": len(records), "rated_response_count": len(eligible), "answer_count": answer_count,
                  "source_ids": [row["id"] for row in eligible]}
        denominator = answer_count if mode == "questions" or index_id == 5 else len(eligible)
        result.update(denominator=denominator, denominator_unit="question responses" if mode == "questions" or index_id == 5 else "surveys")
        if index_id == 5:
            promoters = ratings.count(5)
            detractors = sum(rating <= 3 for rating in ratings)
            result.update(promoters=promoters, passives=ratings.count(4), detractors=detractors)
            exact = Fraction(100 * (promoters - detractors), answer_count) if answer_count else None
        elif index_id == 6:
            if mode == "questions":
                exact = Fraction(sum(ratings), answer_count) if answer_count else None
            else:
                exact = sum((row["reporting_value"] for row in eligible), Fraction()) / len(eligible) if eligible else None
        else:
            threshold = {1: 4, 2: 5, 3: 3, 4: 2}[index_id]
            if mode == "questions":
                good = sum(rating >= threshold for rating in ratings)
                exact = Fraction(100 * good, answer_count) if answer_count else None
                result["positive_answer_count"] = good
            else:
                survey_values = [_index_round(Fraction(100 * sum(rating >= threshold for rating in row["ratings"]), len(row["ratings"]))) for row in eligible]
                exact = Fraction(sum(survey_values), len(eligible)) if eligible else None
        result["value"] = _index_round(exact, 2 if index_id == 6 else 0) if exact is not None else None
        return result

    summary = summarize(prepared)
    label = REPORTING_INDEX_NAMES[index_id]
    def readout(result, group=None):
        subject = f"{group}: " if group is not None else ""
        if result["value"] is None:
            return subject + f"No eligible ratings are available for {scope}."
        value = f"{result['value']:.2f}" if index_id == 6 else str(result["value"])
        unit = " out of 5" if index_id == 6 else ("" if index_id == 5 else "%")
        count_unit = result["denominator_unit"] if result["denominator"] != 1 else ("question response" if result["denominator_unit"] == "question responses" else "survey")
        measure = label.lower() if index_id == 6 else (label if index_id == 5 else "score")
        definition = "" if index_id in (5, 6) else f" ({label})"
        text = subject + f"Your {measure} for {scope} was {value}{unit}{definition}, based on {result['denominator']} {count_unit}."
        if index_id == 6 and all(questions[key]["direction"] == "lower" for key in active):
            text += " Lower is better for these questions."
        return text
    output = {"state": "complete", "scope": scope, "index": {"id": index_id, "name": label, "source": origin, "basis": pref["basis"]},
              "aggregation": dict(aggregation), "verification_scope": "Caller-provided source and reporting context; not automatic account preference discovery.",
              "result": summary, "readout": readout(summary)}
    if group_by is not None:
        output["groups"] = [{"group_value": group["value"], "result": summarize(group["rows"])} for group in groups.values()]
        output["readout"] += "\n" + "\n".join(readout(group["result"], group["group_value"]) for group in output["groups"])
    return output


def reporting_index_main(argv):
    parser = argparse.ArgumentParser(description="Apply a verified GuildQuality reporting index to a bounded selected feedback cohort; no API or credentials.", allow_abbrev=False)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--group-by")
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not args.input.is_file():
            raise CalculationError("Reporting input must be a regular readable JSON file.")
        with args.input.open("rb") as handle:
            raw = handle.read(SNAPSHOT_MAX_BYTES + 1)
        if len(raw) > SNAPSHOT_MAX_BYTES:
            raise CalculationError("Reporting input byte budget exceeded.")
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_snapshot_json_pairs, parse_constant=_snapshot_json_constant)
        result = calculate_reporting_index(payload, args.group_by)
        print(json.dumps(result if args.details else {key: result[key] for key in ("state", "readout")}, allow_nan=False))
        return 0
    except CalculationError as error:
        print(json.dumps({"error": str(error)}))
        return 2
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError):
        print(json.dumps({"error": "Reporting calculation refused: check the verified index, question definitions, aggregation and source answers."}))
        return 2


def evidence_main(argv):
    parser = argparse.ArgumentParser(description="Check explicit CSV theme memberships and count their actual scope; no classification, API or credentials.", allow_abbrev=False)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args(argv)
    try:
        def bounded(path):
            if not path.is_file():
                raise CalculationError("Evidence inputs must be regular readable files.")
            with path.open("rb") as handle:
                raw = handle.read(SNAPSHOT_MAX_BYTES + 1)
            if len(raw) > SNAPSHOT_MAX_BYTES:
                raise CalculationError("Evidence input byte budget exceeded.")
            return raw
        spec = json.loads(bounded(args.spec).decode("utf-8"), object_pairs_hook=_snapshot_json_pairs,
                          parse_constant=_snapshot_json_constant, parse_int=_evidence_number, parse_float=_evidence_number)
        result = count_csv_evidence(bounded(args.csv), spec)
        if not args.details:
            grouping = result.get("grouping")
            result = {"state": result["state"], "count_unit": result["count_unit"],
                      "record_unit_basis": result["record_unit_basis"], "scope_record_count": result["scope_record_count"],
                      "verification_scope": result["verification_scope"], "classification_basis": result["classification_basis"],
                      "scope_label": result["scope_label"], "scope_response_count": result["scope_response_count"],
                      "themes": [{key: value for key, value in theme.items() if key != "evidence"} for theme in result["themes"]]}
            if grouping is not None:
                result["grouping"] = {key: value for key, value in grouping.items() if key != "field"}
                for theme in result["themes"]:
                    theme["grouping"]["groups"] = [{key: value for key, value in group.items() if key != "source_ids"}
                                                      for group in theme["grouping"]["groups"]]
        print(json.dumps(result, allow_nan=False))
        return 0
    except CalculationError as error:
        print(json.dumps({"error": str(error)}))
        return 2
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError):
        print(json.dumps({"error": "Evidence count refused: check CSV shape, explicit mappings, filters and quoted memberships."}))
        return 2


def calendar_main(argv):
    parser = argparse.ArgumentParser(description="Resolve a full calendar month from an explicit local date; returned since/until dates are inclusive. No clock, source inference, API or credentials.", allow_abbrev=False)
    parser.add_argument("--reference-date", required=True, help="Explicit local calendar date in YYYY-MM-DD form")
    parser.add_argument("--relative", required=True, choices=("previous-month", "current-month", "next-month"))
    args = parser.parse_args(argv)
    try:
        print(json.dumps(calendar_period(args.reference_date, args.relative), allow_nan=False))
        return 0
    except CalculationError as error:
        print(json.dumps({"error": str(error)}))
        return 2


def snapshot_main(argv):
    parser = argparse.ArgumentParser(description="Bounded NPS on an explicitly supplied snapshot; no dates, API or credentials.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--group-by", help="An actual observed field, such as month; does not invent dates or scope scenarios")
    parser.add_argument("--details", action="store_true", help="Return full computed fields, source IDs and formulas; the default returns a business readout including any requested scenarios")
    args = parser.parse_args(argv)
    try:
        if not args.input.is_file():
            raise CalculationError("Snapshot input must be a regular readable JSON file.")
        with args.input.open("rb") as handle:
            raw = handle.read(SNAPSHOT_MAX_BYTES + 1)
        if len(raw) > SNAPSHOT_MAX_BYTES:
            raise CalculationError("Snapshot input byte budget exceeded.")
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_snapshot_json_pairs,
                             parse_constant=_snapshot_json_constant)
        result = calculate_snapshot(payload, args.group_by)
        display = dict(result, response_count_unit="survey responses, not distinct people", readout=snapshot_readout(result), source_readout=snapshot_source_readout(result)) if args.details else {"state": "complete", "readout": snapshot_readout(result)}
        print(json.dumps(display, allow_nan=False))
        return 0
    except CalculationError as error:
        print(json.dumps({"error": str(error)}))
        return 2
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError):
        print(json.dumps({"error": "Snapshot calculation refused: check the supplied JSON, cohort, source IDs and verified recommendation definition."}))
        return 2

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "report-index":
        return reporting_index_main(sys.argv[2:])
    if len(sys.argv) > 1 and sys.argv[1] == "evidence-count":
        return evidence_main(sys.argv[2:])
    if len(sys.argv) > 1 and sys.argv[1] == "calendar-period":
        return calendar_main(sys.argv[2:])
    if len(sys.argv) > 1 and sys.argv[1] == "snapshot-nps":
        return snapshot_main(sys.argv[2:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--metric", choices=("nps", "response-rate", "count"), default="nps")
    parser.add_argument("--question-id")
    parser.add_argument("--since", required=True)
    parser.add_argument("--until", required=True)
    parser.add_argument("--timezone", default="America/New_York")
    parser.add_argument("--include-imported", action="store_true", help="Include imported records only when the declared metric definition requires them")
    parser.add_argument("--observation", choices=("period-end", "current"), default="period-end", help="Completed by period end, or current status in the supplied records")
    parser.add_argument("--denominator", choices=("sent-status", "attempted"), default="sent-status", help="Sent lifecycle statuses, or surveys with explicit outreach-attempt records (not confirmed delivery)")
    parser.add_argument("--observed-as-of", help="Source observation timestamp; defaults to the retrieval wrapper's retrieved_at for response rates")
    parser.add_argument("--latest-in-period", action="store_true", help="Latest completed survey per supplied stable contact ID within this period after import policy; not global app latest")
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > 16_000_000:
            raise CalculationError("Input byte budget exceeded.")
        payload = json.loads(args.input.read_text())
        rows = payload.get("data") if isinstance(payload, dict) else payload
        result = calculate(rows, args.metric, args.question_id, args.since, args.until, args.timezone,
                           isinstance(payload, dict) and payload.get("pagination_complete") is True, exclude_imported=not args.include_imported,
                           observation=args.observation, denominator=args.denominator,
                           observed_as_of=args.observed_as_of or (payload.get("retrieved_at") if args.metric == "response-rate" and isinstance(payload, dict) else None),
                           latest_in_period=args.latest_in_period)
        print(json.dumps(result, allow_nan=False))
        return 0
    except CalculationError as error:
        # CalculationError messages are controlled diagnostics, never source text.
        print(json.dumps({"error": str(error)}))
        return 2
    except (OSError, ValueError, TypeError, KeyError):
        print(json.dumps({"error": "Calculation refused: check record shape, dates, timezone and verified question scale."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
