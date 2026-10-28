#!/usr/bin/env python3
"""Bounded arithmetic on retrieved survey records; no network or credential access."""
import argparse
from datetime import date, datetime
import json
import math
from pathlib import Path
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class CalculationError(ValueError):
    pass


def local_day(value, timezone):
    if not value:
        return None
    text = str(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return date.fromisoformat(text)
    for suffix, offset in ((" EDT", "-04:00"), (" EST", "-05:00"), (" UTC", "+00:00"), (" GMT", "+00:00")):
        if text.endswith(suffix):
            text = text[:-len(suffix)] + offset
            break
    try:
        instant = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if instant.tzinfo is None:
            raise CalculationError("Timestamp needs an explicit offset or supported source timezone.")
        return instant.astimezone(ZoneInfo(timezone)).date()
    except (ValueError, ZoneInfoNotFoundError):
        raise CalculationError("Unsupported date/timezone in selected source records.") from None


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


def calculate(rows, metric="nps", question_id=None, since=None, until=None,
              timezone="America/New_York", complete=False, exclude_imported=True):
    if type(exclude_imported) is not bool:
        raise CalculationError("Imported-survey policy must be explicit boolean metadata.")
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
    if len(ids) != len(rows) or None in ids or len(set(ids)) != len(ids):
        raise CalculationError("Survey records require unique stable source IDs.")
    def in_period(value):
        day = local_day(value, timezone)
        return day is not None and lower <= day <= upper
    policy = "exclude imported surveys" if exclude_imported else "include imported surveys"
    base = {"import_policy": policy, "metric": metric, "since": since, "until": until, "timezone": timezone,
            "input_complete": complete is True, "retrieved_rows": len(rows),
            "coverage_basis": "Selected retrieved records; completeness applies only to their source queries."}
    if metric == "response-rate":
        cohort = [r for r in rows if (not exclude_imported or not r.get("isImported"))
                  and str(r.get("status", "")).lower().replace(" ", "-") in ("in-progress", "completed", "abandoned", "no-response")
                  and in_period(r.get("sendAt"))]
        completed = [r for r in cohort if str(r.get("status", "")).lower() == "completed"
                     and local_day(r.get("endedAt"), timezone) is not None
                     and local_day(r["endedAt"], timezone) <= upper]
        base.update(sent_count=len(cohort), cohort_completed_count=len(completed),
                    response_rate=100 * len(completed) / len(cohort) if cohort else None,
                    cohort_source_ids=sorted(r["id"] for r in cohort),
                    completed_source_ids=sorted(r["id"] for r in completed),
                    observation_cutoff=until, import_policy=policy)
        return base
    completed = [r for r in rows if str(r.get("status", "")).lower() == "completed"
                 and (not exclude_imported or not r.get("isImported")) and in_period(r.get("endedAt"))]
    if metric == "count":
        base.update(completed_count=len(completed), source_ids=sorted(r["id"] for r in completed))
        return base
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
    base.update(nps=100 * (promoters - detractors) / len(values) if values else None,
                n=len(values), promoters=promoters, passives=len(values)-promoters-detractors,
                detractors=detractors, source_ids=sorted(i for i, _ in values),
                excluded_completed_count=len(completed)-len(values),
                import_policy=policy, question_id=question_id)
    return base


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--metric", choices=("nps", "response-rate", "count"), default="nps")
    parser.add_argument("--question-id")
    parser.add_argument("--since", required=True)
    parser.add_argument("--until", required=True)
    parser.add_argument("--timezone", default="America/New_York")
    parser.add_argument("--include-imported", action="store_true", help="Include imported records only when the declared metric definition requires them")
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > 16_000_000:
            raise CalculationError("Input byte budget exceeded.")
        payload = json.loads(args.input.read_text())
        rows = payload.get("data") if isinstance(payload, dict) else payload
        result = calculate(rows, args.metric, args.question_id, args.since, args.until, args.timezone,
                           isinstance(payload, dict) and payload.get("pagination_complete") is True, exclude_imported=not args.include_imported)
        print(json.dumps(result, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError):
        print(json.dumps({"error": "Calculation refused: check record shape, dates, timezone and verified question scale."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
