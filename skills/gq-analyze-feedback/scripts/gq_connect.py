#!/usr/bin/env python3
"""Private, explicit-profile customer setup and reporting; no action interface.

This local interactive workflow does not supply a hosted private-entry facility.
The account connection is separate from the installed skill files.
"""
import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
from statistics import median
import time
from urllib.parse import urlencode, urlsplit

import gq_api as api
import gq_transport as transport
from gq_transport import ClientError

ENVIRONMENT = "customer-connection"
MAX_REPORT_CHOICES = 50
MAX_PROFILE_BYTES = 65536


def profile_path(value):
    path = Path(value).expanduser().absolute()
    if path.is_symlink() or path.parent.is_symlink():
        raise ClientError("Profile and private directory must not be symlinks.")
    path = path.resolve()
    installed = Path(__file__).resolve().parent.parent
    if path == installed or installed in path.parents:
        raise ClientError("Keep the connection profile outside the installed skill.")
    if any(os.path.lexists(parent / ".git") for parent in path.parents):
        raise ClientError("Keep the connection profile outside Git repositories so credentials are not committed.")
    if path.name in ("token", "environment.json", "state"):
        raise ClientError("Choose a separate profile filename, such as connection.json.")
    return path


def positive_id(value):
    if isinstance(value, bool) or not re.fullmatch(r"[1-9][0-9]{0,17}", str(value)):
        raise ClientError("Account, company, and report IDs must be positive numeric IDs.")
    return int(value)


def validate_scope(kind, origin, account_id, company_ids):
    account_id = positive_id(account_id)
    if isinstance(company_ids, str):
        company_ids = company_ids.split(",")
    if not isinstance(company_ids, list) or not company_ids or len(company_ids) > 100:
        raise ClientError("Supply a bounded explicit company scope including the root account.")
    companies = [positive_id(v.strip() if isinstance(v, str) else v) for v in company_ids]
    if len(companies) != len(set(companies)) or account_id not in companies:
        raise ClientError("Company scope must be unique and include the root account.")
    if kind == "production":
        if origin not in (None, "https://www.guildquality.com", "https://www.guildquality.com/"):
            raise ClientError("Production uses only its fixed GuildQuality origin.")
        origin = "https://www.guildquality.com"
    elif kind == "staging":
        if not isinstance(origin, str):
            raise ClientError("Staging requires its explicitly approved exact HTTPS origin.")
        parsed = urlsplit(origin)
        if (parsed.scheme != "https" or parsed.username or parsed.password or parsed.port is not None
                or parsed.query or parsed.fragment or parsed.path not in ("", "/")
                or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.www\.guildquality\.com", parsed.netloc)):
            raise ClientError("Staging must use an exact approved GuildQuality branch/sandbox HTTPS origin.")
        origin = "https://" + parsed.netloc
    else:
        raise ClientError("Select production or staging explicitly.")
    return origin, account_id, companies


def private_json(path):
    transport._private_stat(path.parent.lstat(), directory=True)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, encoding="utf-8") as stream:
        info = os.fstat(stream.fileno())
        transport._private_stat(info)
        if info.st_size > MAX_PROFILE_BYTES:
            raise ClientError("Connection configuration is unexpectedly large.")
        raw = stream.read(MAX_PROFILE_BYTES + 1)
    if len(raw) > MAX_PROFILE_BYTES:
        raise ClientError("Connection configuration is unexpectedly large.")
    return json.loads(raw)


def credential_reference(path):
    return "GQ_CONNECT_" + hashlib.sha256(str(path).encode()).hexdigest()[:16].upper() + "_TOKEN_FILE"


def load_profile(filename):
    path = profile_path(filename)
    profile = private_json(path)
    if (not isinstance(profile, dict) or profile.get("schema_version") != 1
            or profile.get("environment_id") != ENVIRONMENT
            or profile.get("credential_reference") != credential_reference(path)
            or not isinstance(profile.get("last_check"), dict)):
        raise ClientError("Unsupported or relocated connection profile; review its private configuration.")
    manifest_path = path.parent / "environment.json"
    manifest = private_json(manifest_path)
    if (not isinstance(manifest, dict) or manifest.get("schema_version") != 1
            or not isinstance(manifest.get("environments"), dict)
            or set(manifest["environments"]) != {ENVIRONMENT}):
        raise ClientError("Unexpected connection environment configuration.")
    env = manifest["environments"][ENVIRONMENT]
    if not isinstance(env, dict):
        raise ClientError("Connection environment must be an object.")
    base = env.get("base_url", "")
    if not isinstance(base, str) or not base.endswith("/company-api/v3"):
        raise ClientError("Connection has an invalid API base.")
    origin, account, companies = validate_scope(env.get("kind"), base[:-len("/company-api/v3")],
                                               env.get("account_id"), env.get("allowed_company_ids"))
    if (manifest.get("approved_origins") != {ENVIRONMENT: origin}
            or env.get("credential") != {"file_env": profile["credential_reference"]}
            or env.get("state_dir") != str(path.parent / "state")
            or env.get("actions_authorized") is not False):
        raise ClientError("Connection origin, private source, or reporting-only configuration changed.")
    return path, profile, manifest, env


@contextmanager
def private_reference(path, profile):
    variable = profile["credential_reference"]
    prior = os.environ.get(variable)
    os.environ[variable] = str(path.parent / "token")
    try:
        yield
    finally:
        if prior is None:
            os.environ.pop(variable, None)
        else:
            os.environ[variable] = prior


def redact(value, secret):
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]")
    if isinstance(value, list):
        return [redact(v, secret) for v in value]
    if isinstance(value, dict):
        return {str(k).replace(secret, "[REDACTED]"): ("[REDACTED]" if str(k).lower() in
                ("authorization", "token", "api_token", "access_token") else redact(v, secret)) for k, v in value.items()}
    return value


def report_choices(payload, secret):
    if not (isinstance(payload, list) or isinstance(payload, dict) and isinstance(payload.get("data"), list)):
        raise ClientError("Reports returned an unsupported shape; no account binding was created.")
    rows = api.records(payload)
    if len(rows) > 500:
        raise ClientError("Too many reports for bounded setup; provide a reviewed account configuration.")
    choices = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise ClientError("Reports lack a usable identity marker.")
        name = row["name"]
        if not name.strip() or len(name) > 256 or secret in name or any(ord(c) < 32 or ord(c) == 127 for c in name):
            raise ClientError("Report names cannot be safely presented for binding.")
        choices.append({"report_id": positive_id(row.get("id")), "report_name": name})
    return choices


def status(filename):
    path = profile_path(filename)
    if not path.exists():
        return {"configured": False, "state": "not-configured", "profile": str(path),
                "next_step": "Run setup yourself in a private interactive terminal; never enter the key in chat."}
    path, profile, manifest, env = load_profile(path)
    token = path.parent / "token"
    try:
        transport._private_stat(token.lstat())
        credential_present = True
    except (OSError, ClientError):
        credential_present = False
    last = profile.get("last_check", {"verified": False, "reason": "not-checked"})
    return {"configured": True, "state": "missing-credential" if not credential_present else
                "verified" if last.get("verified") is True else "configured-unverified",
            "profile": str(path), "kind": env["kind"], "origin": env["base_url"][:-len("/company-api/v3")],
            "account_id": env["account_id"], "allowed_company_ids": env["allowed_company_ids"],
            "network_checked": False, "verification_is_last_check_only": True,
            "credential_source": "private-file", "credential_file": str(token), "credential_present": credential_present,
            "report_marker": env.get("identity_marker"), "last_check": last,
            "identity_limit": "Root/scope were explicitly selected by the customer; report-marker verification is not a root identity endpoint.",
            "hosted_private_entry_and_persistence": "not-established-by-this-local-helper"}


def save_check(path, profile, verified, reason, choices=None):
    profile["last_check"] = {"verified": verified, "reason": reason, "checked_at": time.time()}
    api.private_write(path, profile, exclusive=False)
    result = status(path)
    if choices is not None:
        result["report_choices"] = choices[:MAX_REPORT_CHOICES]
        result["choices_truncated"] = len(choices) > MAX_REPORT_CHOICES
    return result


def preflight(filename, report_id=None, report_name=None, interactive=False, transport_fn=None):
    if (report_id is None) != (report_name is None):
        raise ClientError("Supply the report ID and exact name together, or select an offered report privately.")
    path, profile, manifest, env = load_profile(filename)
    with private_reference(path, profile):
        secret = api.credential_for(env)
        try:
            payload = (transport_fn("GET", env["base_url"] + "/reports", None) if transport_fn else
                       transport.request_json("GET", env["base_url"] + "/reports", secret,
                                              base_url=env["base_url"], timeout=15, max_bytes=1_000_000))
            choices = report_choices(payload, secret)
            marker = ({"report_id": positive_id(report_id), "report_name": report_name} if report_id is not None
                      else env.get("identity_marker"))
            if marker is None and choices and interactive:
                print(json.dumps({"report_choices": choices[:MAX_REPORT_CHOICES]}, ensure_ascii=False), file=sys.stderr)
                selected = positive_id(input("Select an existing report ID to bind this connection (no key): "))
                matches = [choice for choice in choices[:MAX_REPORT_CHOICES] if choice["report_id"] == selected]
                marker = matches[0] if len(matches) == 1 else None
            if marker is None:
                return save_check(path, profile, False, "no-visible-reports" if not choices else "report-selection-required", choices)
            matches = [choice for choice in choices if str(choice["report_id"]) == str(marker.get("report_id"))
                       and choice["report_name"] == marker.get("report_name")]
            if len(matches) != 1:
                return save_check(path, profile, False, "report-marker-mismatch", choices)
            env["identity_marker"] = matches[0]
            env["allowed_report_ids"] = [matches[0]["report_id"]]
            env["approved"] = True
            api.private_write(path.parent / "environment.json", manifest, exclusive=False)
            client = api.Client(path.parent / "environment.json", ENVIRONMENT, mode="reporting", transport_fn=transport_fn)
            client.preflight()
            return save_check(path, profile, True, "exact-report-marker-verified")
        except ClientError as error:
            result = save_check(path, profile, False, "connection-or-binding-check-failed")
            result.update(transport.safe_error_diagnostic(error))
            return result
        except (OSError, ValueError, TypeError, KeyError, EOFError):
            return save_check(path, profile, False, "connection-or-binding-check-failed")


def setup(filename, kind, account_id, company_ids, origin=None, report_id=None, report_name=None, transport_fn=None):
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        raise ClientError("Setup needs your own private interactive terminal; no piped or chat key input is accepted.")
    origin, account, companies = validate_scope(kind, origin, account_id, company_ids)
    if (report_id is None) != (report_name is None):
        raise ClientError("Supply both expected report ID and name, or select from reports after private entry.")
    if report_id is not None:
        positive_id(report_id)
    path = profile_path(filename)
    api.private_dir(path.parent)
    for target in (path, path.parent / "token", path.parent / "environment.json", path.parent / "state"):
        if target.exists() or target.is_symlink():
            raise ClientError("Connection files already exist; setup never overwrites credentials or configuration.")
    profile = {"schema_version": 1, "environment_id": ENVIRONMENT,
               "credential_reference": credential_reference(path),
               "last_check": {"verified": False, "reason": "private-entry-pending"}}
    env = {"approved": False, "authorization_ref": "customer-selected-profile:" + credential_reference(path),
           "kind": kind, "base_url": origin + "/company-api/v3", "account_id": account,
           "allowed_company_ids": companies, "credential": {"file_env": profile["credential_reference"]},
           "identity_marker": None, "state_dir": str(path.parent / "state"),
           "read_record_ids": {"surveys": [], "reviews": []}, "write_record_ids": {"surveys": [], "reviews": []},
           "allowed_report_ids": [], "actions_authorized": False}
    manifest = {"schema_version": 1, "approved_origins": {ENVIRONMENT: origin}, "environments": {ENVIRONMENT: env}}
    transport.setup_token(str(path.parent / "token"))
    api.private_write(path.parent / "environment.json", manifest)
    api.private_write(path, profile)
    api.private_dir(path.parent / "state")
    return preflight(path, report_id, report_name, interactive=report_id is None, transport_fn=transport_fn)


def _numeric_date(value):
    if value is None or value == "":
        return value
    pattern = (r"[0-9]{4}-[0-9]{2}-[0-9]{2}(?:T[0-9]{2}:[0-9]{2}:[0-9]{2}"
               r"(?:[.][0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2}| "
               r"(?:UTC|GMT|EST|EDT|CST|CDT|MST|MDT|PST|PDT))?)?")
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ClientError("Numeric projection contains an unsupported date.")
    try:
        datetime.fromisoformat(value.split(" ")[0].replace("Z", "+00:00"))
    except ValueError:
        raise ClientError("Numeric projection contains an invalid date.") from None
    return value


def _numeric_choice(value, allowed):
    if value is None or value == "":
        return value
    if not isinstance(value, str) or value not in allowed:
        raise ClientError("Numeric projection contains an unsupported structured value.")
    return value


def _numeric_rating(value):
    # Preserve missing/empty values and the original integer numeric representation.
    # A nonnumeric answer is never converted to zero or forwarded as free text.
    if value is None or value == "":
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ClientError("Numeric projection contains an unsupported rating.")
    if isinstance(value, str) and not re.fullmatch(r"(?:10|[0-9])(?:[.]0+)?", value):
        raise ClientError("Numeric projection contains a noninteger rating.")
    try:
        number = float(value)
    except (OverflowError, ValueError):
        raise ClientError("Numeric projection contains an unsupported rating.") from None
    if not math.isfinite(number) or not 0 <= number <= 10 or not number.is_integer():
        raise ClientError("Numeric projection contains a noninteger rating.")
    return value


def _numeric_optional_id(value):
    if value is None or value == "":
        return value
    positive_id(value)
    return value


def _numeric_label(value, maximum):
    # Template/question definition labels are schema metadata, not answers. They
    # remain untrusted plain text: never interpret HTML, follow links or execute it.
    if value is not None and (not isinstance(value, str) or len(value) > maximum or "@" in value
                              or "://" in value or "<" in value or ">" in value
                              or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise ClientError("Numeric projection contains an unsafe definition label.")
    return value


def _numeric_survey(row):
    if not isinstance(row, dict) or "id" not in row:
        raise ClientError("Numeric projection requires an identifiable survey object.")
    positive_id(row["id"])
    output = {"id": row["id"]}
    for key in ("companyId", "contactId"):
        if key in row:
            output[key] = _numeric_optional_id(row[key])
    for key in ("company", "contact"):
        if key in row:
            nested = row[key]
            if nested is None:
                output[key] = None
            elif isinstance(nested, dict):
                output[key] = {"id": _numeric_optional_id(nested["id"])} if "id" in nested else {}
            else:
                raise ClientError("Numeric projection contains an unsupported identity object.")
    if "template" in row:
        output["template"] = _numeric_label(row["template"], 256)
    if "status" in row:
        output["status"] = _numeric_choice(row["status"], {"Scheduled", "In progress", "Completed", "Abandoned", "No response"})
    if "isImported" in row:
        if row["isImported"] is not None and type(row["isImported"]) is not bool:
            raise ClientError("Numeric projection contains an unsupported import flag.")
        output["isImported"] = row["isImported"]
    for key in ("sendAt", "endedAt", "createdAt", "updatedAt", "lastActivityAt"):
        if key in row:
            output[key] = _numeric_date(row[key])
    if "questions" in row:
        questions = row["questions"]
        if questions is None:
            output["questions"] = None
        elif not isinstance(questions, list) or len(questions) > 1000:
            raise ClientError("Numeric projection contains unsupported questions.")
        else:
            output["questions"] = []
            seen = set()
            for question in questions:
                if not isinstance(question, dict) or "questionId" not in question:
                    raise ClientError("Numeric projection requires identifiable questions.")
                qid = positive_id(question["questionId"])
                if qid in seen:
                    raise ClientError("Numeric projection contains duplicate question IDs.")
                seen.add(qid)
                projected = {"questionId": question["questionId"]}
                if "name" in question:
                    projected["name"] = _numeric_label(question["name"], 512)
                for key, allowed in (("type", {"rating", "comment", "mcs", "mcm"}), ("ratingScale", {"0-10", "1-5"})):
                    if key in question:
                        projected[key] = _numeric_choice(question[key], allowed)
                if "rating" in question:
                    projected["rating"] = _numeric_rating(question["rating"])
                output["questions"].append(projected)
    if "attempts" in row:
        attempts = row["attempts"]
        if attempts is None:
            output["attempts"] = None
        elif not isinstance(attempts, list) or len(attempts) > 10000:
            raise ClientError("Numeric projection contains unsupported attempts.")
        else:
            output["attempts"] = []
            for attempt in attempts:
                if not isinstance(attempt, dict):
                    raise ClientError("Numeric projection contains an unsupported attempt.")
                projected = {}
                if "type" in attempt:
                    projected["type"] = _numeric_choice(attempt["type"], {"email", "text", "phone", "incoming_phone", "mail", "ai_phone"})
                if "createdAt" in attempt:
                    projected["createdAt"] = _numeric_date(attempt["createdAt"])
                output["attempts"].append(projected)
    return output


def numeric_projection(result):
    """Minimize a checked survey result without claiming omitted fields are empty.

    Numeric questions retain template and question-definition labels so callers
    can inspect their meaning. Omitted comments/contacts are not empty answers.
    This is field minimization, not anonymization, account authorization or an
    independent identity check. Client scope/completeness checks run first.
    """
    if not isinstance(result, dict) or "data" not in result:
        raise ClientError("Numeric projection requires a checked survey result.")
    data = result["data"]
    if isinstance(data, list):
        projected = [_numeric_survey(row) for row in data]
    elif isinstance(data, dict) and "data" in data and isinstance(data["data"], dict) and "id" not in data:
        projected = {"data": _numeric_survey(data["data"])}
    elif isinstance(data, dict):
        projected = _numeric_survey(data)
    else:
        raise ClientError("Numeric projection contains an unsupported survey response.")
    output = {"data": projected, "projection": "numeric"}
    for key in ("pages_fetched", "page", "current_page", "last_page", "per_page", "total"):
        if key in result:
            value = result[key]
            if value is not None and (type(value) is not int or value < 0):
                raise ClientError("Numeric projection contains invalid pagination metadata.")
            output[key] = value
    if "pagination_complete" in result:
        value = result["pagination_complete"]
        if value is not None and type(value) is not bool:
            raise ClientError("Numeric projection contains invalid completeness metadata.")
        output["pagination_complete"] = value
    if "source_ids" in result:
        if not isinstance(result["source_ids"], list):
            raise ClientError("Numeric projection contains invalid source IDs.")
        for value in result["source_ids"]:
            positive_id(value)
        output["source_ids"] = list(result["source_ids"])
    if "applied_company_ids" in result:
        values = result["applied_company_ids"]
        if (not isinstance(values, list) or not 1 <= len(values) <= 100
                or any(type(value) is not int or value <= 0 or value > 10 ** 18 - 1 for value in values)
                or len(set(values)) != len(values)):
            raise ClientError("Numeric projection contains invalid applied company scope.")
        output["applied_company_ids"] = list(values)
    if "company_scope_source" in result:
        value = result["company_scope_source"]
        if not isinstance(value, str) or value not in ("profile_default", "explicit_filter"):
            raise ClientError("Numeric projection contains invalid company scope provenance.")
        output["company_scope_source"] = value
    if "elapsed_seconds" in result:
        value = result["elapsed_seconds"]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ClientError("Numeric projection contains invalid retrieval timing.")
        output["elapsed_seconds"] = value
    if "retrieved_at" in result:
        output["retrieved_at"] = _numeric_date(result["retrieved_at"])
    if "stop_reason" in result:
        output["stop_reason"] = _numeric_choice(result["stop_reason"], {
            "pagination_loop", "time_budget", "request_failed", "unexpected_page_shape", "pagination_metadata_absent",
            "duplicate_source_ids", "row_budget", "end_of_pages", "single_page_requested", "retrieval_budget", "unsafe_next_link"})
    if "environment_id" in result:
        if result["environment_id"] != ENVIRONMENT:
            raise ClientError("Numeric projection contains an unexpected profile environment.")
        output["environment_id"] = result["environment_id"]
    if result.get("error"):
        output["error"] = "Survey retrieval did not complete; see completeness and stop_reason."
        code = result.get("error_code")
        if isinstance(code, str) and code in transport.ERROR_DIAGNOSTICS:
            output.update(error_code=code, error=transport.ERROR_DIAGNOSTICS[code])
    if "survey_owner_attribution" in result:
        proof = result["survey_owner_attribution"]
        if not isinstance(proof, dict):
            raise ClientError("Numeric projection contains invalid ownership attribution.")
        safe_proof = {}
        for key in ("account_id", "report_id"):
            if key in proof:
                positive_id(proof[key])
                safe_proof[key] = proof[key]
        for key in ("children_empty_verified", "server_fields_modified"):
            if key in proof:
                if type(proof[key]) is not bool:
                    raise ClientError("Numeric projection contains invalid ownership attribution.")
                safe_proof[key] = proof[key]
        if "inferred_source_ids" in proof:
            if not isinstance(proof["inferred_source_ids"], list):
                raise ClientError("Numeric projection contains invalid inferred source IDs.")
            for value in proof["inferred_source_ids"]:
                positive_id(value)
            safe_proof["inferred_source_ids"] = list(proof["inferred_source_ids"])
        if "basis" in proof:
            safe_proof["basis"] = _numeric_choice(proof["basis"], {
                "independent administrator account/report binding plus fresh API report match and empty children"})
        output["survey_owner_attribution"] = safe_proof
    return output


def get(filename, resource, all_pages=False, transport_fn=None, projection=None):
    if projection not in (None, "numeric"):
        raise ClientError("Unsupported output projection; use numeric for survey reads.")
    if projection == "numeric":
        if not isinstance(resource, str):
            raise ClientError("Numeric projection requires an explicit survey path.")
        parsed = urlsplit(resource)
        if (parsed.scheme or parsed.netloc or parsed.fragment
                or not re.fullmatch(r"/surveys(?:/[1-9][0-9]{0,17})?", parsed.path)):
            raise ClientError("Numeric projection supports only survey list or exact survey detail paths.")
    path, profile, manifest, env = load_profile(filename)
    if env.get("approved") is not True or not env.get("identity_marker"):
        raise ClientError("Connection has no verified report binding; run preflight and select an existing report first.")
    with private_reference(path, profile):
        secret = api.credential_for(env)
        client = api.Client(path.parent / "environment.json", ENVIRONMENT, mode="reporting", transport_fn=transport_fn)
        resolved = urlsplit(client.url(resource)).path[len("/company-api/v3"):]
        detail = re.fullmatch(r"/(surveys|reviews)/([1-9][0-9]{0,17})", resolved)
        if detail:
            # Explicit customer read only, temporary for this call. Client validates returned owner/ID.
            client.env["read_record_ids"][detail[1]] = [positive_id(detail[2])]
        result = client.get(resource, all_pages=all_pages)
        return redact(numeric_projection(result) if projection == "numeric" else result, secret)


def _report_analysis():
    # Review-only installations intentionally do not bundle this calculator.
    path = Path(__file__).resolve().parent / "gq_analysis.py"
    if path.is_symlink() or not path.is_file():
        raise ClientError("Numeric reports require the Analyze Feedback skill's bundled calculator; this installation supports only its existing connection commands.")
    specification = importlib.util.spec_from_file_location("gq_bundled_report_analysis", path)
    if specification is None or specification.loader is None:
        raise ClientError("The bundled reporting calculator is unavailable.")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _new_report_directory(value):
    path = Path(value).expanduser().absolute()
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ClientError("Report output must use a new private directory without symlink components.")
    path = path.resolve()
    installed = Path(__file__).resolve().parent.parent
    if path == installed or installed in path.parents:
        raise ClientError("Keep report output outside the installed skill.")
    if any(os.path.lexists(parent / ".git") for parent in path.parents):
        raise ClientError("Keep report output outside Git repositories so source records are not committed.")
    if path.exists() or not path.parent.is_dir():
        raise ClientError("Choose a new report directory in an existing private workspace; existing output is never overwritten.")
    path.mkdir(mode=0o700)
    transport._private_stat(path.lstat(), directory=True)
    return path


def _report_months(lower, upper):
    windows = []
    current = lower.replace(day=1)
    while current <= upper:
        if len(windows) >= 200:
            raise ClientError("Monthly reporting is limited to 200 periods per request.")
        following = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        windows.append((current.strftime("%Y-%m"), max(lower, current), min(upper, following - timedelta(days=1))))
        current = following
    return windows


def _report_summary(calculation, metric, latest_in_period=False):
    if metric == "nps":
        output = {"nps": calculation["nps"], "responses": calculation["n"],
                  "nps_calculation": calculation.get("nps_calculation")}
        categories = [calculation.get(key) for key in ("promoters", "passives", "detractors")]
        if all(type(value) is int and value >= 0 for value in categories) and sum(categories) == calculation["n"]:
            output.update(zip(("promoter_responses", "passive_responses", "detractor_responses"), categories))
        output["response_count_unit"] = "survey responses, not distinct people"
    elif metric == "count":
        output = {"completed": calculation["completed_count"]}
    else:
        output = {"sent": calculation["sent_count"], "completed": calculation["cohort_completed_count"],
                  "response_rate": calculation["response_rate"]}
    summary = calculation.get("contact_summary")
    summary = summary if isinstance(summary, dict) else {}
    def count(key):
        value = summary.get(key)
        return value if type(value) is int and value >= 0 else None
    groups = summary.get("repeated_contact_groups")
    unknown, conflicting = count("unknown_contact_record_count"), count("conflicting_contact_record_count")
    known = count("distinct_known_contact_count")
    output.update(known_contacts=known,
                  contact_identity_complete=summary.get("identity_complete") is True and known is not None and unknown == 0 and conflicting == 0,
                  known_repeat_contact_groups=len(groups) if isinstance(groups, list) else None,
                  unknown_contact_records=unknown, conflicting_contact_records=conflicting)
    if latest_in_period or "selection_policy" in calculation:
        output["contact_counts_basis"] = "Metric-eligible selected records after latest-in-period selection"
        output["selected_known_repeat_contact_groups"] = output.pop("known_repeat_contact_groups")
        if "selection_input_completed_count" in calculation:
            for public, private in (("preselection_completed_count", "selection_input_completed_count"),
                                    ("selected_completed_count", "selection_contact_count"),
                                    ("excluded_earlier_completed_count", "selection_excluded_older_count")):
                value = calculation.get(private)
                output[public] = value if type(value) is int and value >= 0 else None
            original_groups = calculation.get("selection_group_counts")
            output["preselection_contacts_with_multiple_completed"] = (
                sum(group["completed_survey_count"] > 1 for group in original_groups)
                if isinstance(original_groups, list) and all(isinstance(group, dict)
                    and type(group.get("completed_survey_count")) is int and group["completed_survey_count"] > 0
                    for group in original_groups) else None)
            if metric == "nps":
                value = calculation.get("excluded_completed_count")
                output["selected_completed_without_eligible_rating_count"] = value if type(value) is int and value >= 0 else None
    if metric == "response-rate":
        output["response_timing"] = _response_timing(calculation)
    return output


def _contacts_in_multiple_months(monthly):
    contacts = {}
    for month in monthly:
        calculation = month["calculation"]
        summary = calculation.get("contact_summary")
        summary = summary if isinstance(summary, dict) else {}
        records = calculation.get("record_evidence")
        if (calculation.get("input_complete") is not True or summary.get("identity_complete") is not True
                or not isinstance(records, list) or any(not isinstance(record, dict) for record in records)):
            return None
        selected = [record for record in records if record.get("selected_for_metric") is True]
        if len(selected) != summary.get("selected_record_count"):
            return None
        for record in selected:
            identity = record.get("contact")
            if not isinstance(identity, dict) or identity.get("state") != "known":
                return None
            try:
                contact = positive_id(identity.get("id"))
            except ClientError:
                return None
            contacts.setdefault(contact, set()).add(month["period"])
    return sum(len(periods) > 1 for periods in contacts.values())


def _response_timing(calculation):
    expected = calculation.get("cohort_completed_count")
    expected = expected if type(expected) is int and expected >= 0 else None
    output = {"valid_count": 0, "unknown_or_invalid_count": expected, "same_local_day_count": 0,
              "median_elapsed_days": None, "max_elapsed_days": None}
    records = calculation.get("record_evidence")
    if not isinstance(records, list):
        return output
    completed = [record for record in records if isinstance(record, dict)
                 and record.get("selected_for_metric") is True and record.get("completed_in_observation") is True]
    if expected is None or len(completed) != expected:
        return output
    elapsed, same_day, unknown = [], 0, 0
    for record in completed:
        sent, ended = record.get("sendAt"), record.get("endedAt")
        try:
            if not isinstance(sent, dict) or not isinstance(ended, dict) or sent.get("state") != "aware" or ended.get("state") != "aware":
                raise ValueError()
            start = datetime.fromisoformat(sent["utc"].replace("Z", "+00:00"))
            finish = datetime.fromisoformat(ended["utc"].replace("Z", "+00:00"))
            if start.tzinfo is None or finish.tzinfo is None or finish < start:
                raise ValueError()
            sent_day, ended_day = date.fromisoformat(sent["local_date"]), date.fromisoformat(ended["local_date"])
            days = (finish - start).total_seconds() / 86400
            elapsed.append(days)
            same_day += sent_day == ended_day
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            unknown += 1
    output.update(valid_count=len(elapsed), unknown_or_invalid_count=unknown, same_local_day_count=same_day,
                  median_elapsed_days=median(elapsed) if elapsed else None, max_elapsed_days=max(elapsed) if elapsed else None)
    return output


def _readout_number(value, signed=False):
    text = f"{value:.1f}".rstrip("0").rstrip(".") if value else "0"
    return "+" + text if signed and value > 0 else text


def _report_readout(output, analysis=None):
    period = output["period"]
    dates = period["since"] + " to " + period["until"]
    if output.get("state") != "complete":
        return "The requested report for " + dates + " could not be completed; no metrics are reported."
    metric, overall = output["metric"], output["overall"]
    if metric == "nps":
        analysis = analysis or _report_analysis()
        selection_note = None
        if output.get("selection"):
            selection_note = "This counts each person's latest completed response within the requested period."
            before, selected, excluded = (overall.get(key) for key in ("preselection_completed_count", "selected_completed_count", "excluded_earlier_completed_count"))
            if all(type(value) is int and value >= 0 for value in (before, selected, excluded)):
                selection_note += f" {selected} selected from {before} completed responses; {excluded} earlier completed {'response' if excluded == 1 else 'responses'} excluded."
            missing = overall.get("selected_completed_without_eligible_rating_count")
            if type(missing) is int and missing > 0:
                selection_note += f" {missing} selected {'response lacked' if missing == 1 else 'responses lacked'} a valid recommendation rating."
        return analysis.business_recommendation_readout(overall["nps"], overall["responses"],
            period=analysis.business_period(period["since"], period["until"]),
            people=overall.get("known_contacts") if overall.get("contact_identity_complete") is True else None,
            monthly=output.get("monthly"), selection_note=selection_note)
    elif metric == "count":
        text = f"{overall['completed']} {'survey was' if overall['completed'] == 1 else 'surveys were'} completed during {dates}."
        value_key, column, units = "completed", "Completed surveys", ""
    else:
        sent, completed = overall["sent"], overall["completed"]
        attempted = output.get("denominator") == "Surveys with recorded outreach attempts"
        cohort = ("survey" if sent == 1 else "surveys") + " sent during " + dates + (" with recorded outreach attempts" if attempted else "")
        if overall["response_rate"] is None:
            text = f"No eligible {cohort} were found; no response rate is available."
        else:
            cutoff = output.get("observation", "").startswith("Responses recorded by")
            text = (f"By {period['until']}, {completed} of {sent} {cohort} had completed responses ({_readout_number(overall['response_rate'])}%)."
                    if cutoff else f"So far, {completed} of {sent} {cohort} have completed responses ({_readout_number(overall['response_rate'])}%).")
        value_key, column, units = "response_rate", "Completed / sent | Response rate", " percentage points"
    if output.get("selection"):
        text += "\n\nThis uses each person's latest completed response within the requested period"
        before = overall.get("preselection_completed_count")
        selected = overall.get("selected_completed_count")
        excluded = overall.get("excluded_earlier_completed_count")
        if all(type(value) is int and value >= 0 for value in (before, selected, excluded)):
            text += (f": {selected} selected from {before} completed {'response' if before == 1 else 'responses'}; "
                     f"{excluded} earlier completed {'response' if excluded == 1 else 'responses'} excluded.")
            missing = overall.get("selected_completed_without_eligible_rating_count")
            if metric == "nps" and type(missing) is int and missing > 0:
                text += f" {missing} selected {'response lacked' if missing == 1 else 'responses lacked'} an eligible NPS rating."
        else:
            text += "."
    monthly = output.get("monthly")
    if monthly:
        if metric == "response-rate" and output.get("observation", "").startswith("Responses recorded by"):
            text += " Monthly rates use responses recorded by the end of each shown period."
        lines = ["Period | " + column + " | Change", "--- | " + " | ".join("---" for _ in column.split(" | ")) + " | ---"]
        previous = None
        for month in monthly:
            value = month[value_key]
            change = "—" if previous is None or value is None else _readout_number(value - previous, signed=True) + units
            score = "Not available" if value is None else _readout_number(value)
            if metric == "nps":
                cells = f"{score} | {month['responses']}"
            elif metric == "response-rate":
                cells = f"{month['completed']} / {month['sent']} | {score + '%' if value is not None else score}"
            else:
                cells = str(month['completed'])
            lines.append(month["period"] + " | " + cells + " | " + change)
            previous = value
        text += "\n\n" + "\n".join(lines)
    selected_count = overall.get("responses", overall.get("sent", overall.get("completed")))
    if overall.get("contact_identity_complete") is True and overall.get("known_contacts") is not None and overall["known_contacts"] < selected_count:
        if metric != "nps":
            text += (f"\n\nThe {selected_count} {'surveys went to' if metric == 'response-rate' else 'completed responses came from'} "
                     f"{overall['known_contacts']} {'person' if overall['known_contacts'] == 1 else 'people'}.")
    timing = overall.get("response_timing")
    if isinstance(timing, dict) and timing.get("valid_count") and timing.get("unknown_or_invalid_count") == 0:
        text += (f"\n\nOf the completed responses, {timing['same_local_day_count']} arrived on the send date; "
                 f"median elapsed time was {_readout_number(timing['median_elapsed_days'])} {'day' if timing['median_elapsed_days'] == 1 else 'days'} "
                 f"and the maximum was {_readout_number(timing['max_elapsed_days'])} {'day' if timing['max_elapsed_days'] == 1 else 'days'}.")
    return text


def _report_source_readout(output, evidence, analysis):
    if output.get("state") != "complete":
        return "There isn't a completed feedback report for this period, so I can't verify its figures yet."
    period, overall = output["period"], output["overall"]
    dates = analysis.business_period(period["since"], period["until"])
    if output["metric"] == "nps":
        n = overall["responses"]
        text = f"I used {n} completed survey {'response' if n == 1 else 'responses'} with a valid recommendation rating for {dates}. Each response is counted in the month the survey was completed."
        if output.get("selection"):
            text += " Only each person's latest completed response within that period is included."
    elif output["metric"] == "count":
        text = f"I counted {overall['completed']} completed survey {'response' if overall['completed'] == 1 else 'responses'} during {dates}, using when each survey was completed."
    else:
        text = f"I used surveys sent during {dates}. "
        if evidence.get("observation") == "period-end":
            text += f"{overall['completed']} of {overall['sent']} had completed responses by {analysis.business_period(period['until'], period['until'])}."
        else:
            text += f"{overall['completed']} of {overall['sent']} have completed responses in their latest recorded results."
        if evidence.get("denominator") == "attempted":
            text += " This includes only surveys with recorded outreach attempts."
    if evidence.get("import_policy") == "exclude imported surveys":
        text += " Imported feedback was excluded."
    elif evidence.get("import_policy") == "include imported surveys":
        text += " Imported feedback was not excluded."
    return text


def report(filename, metric, since, until, output_dir, *, timezone="America/New_York", question_id=None,
           by_month=False, observation=None, denominator="sent-status", include_imported=False,
           latest_in_period=False, transport_fn=None):
    """Retrieve one numeric cohort and calculate exact local periods privately."""
    analysis = _report_analysis()
    if any(type(value) is not bool for value in (by_month, include_imported, latest_in_period)):
        raise ClientError("Report switches require explicit boolean values.")
    if metric not in ("nps", "count", "response-rate") or (latest_in_period and metric == "response-rate"):
        raise ClientError("Reports support NPS, completed counts, or response rate; latest-per-contact selection applies only to NPS and counts.")
    if observation is None:
        observation = "current" if metric == "response-rate" else "period-end"
    if question_id is not None and metric != "nps":
        raise ClientError("A question ID applies only to NPS reports.")
    # GuildQuality product Question::ID_LTR is 1. This default does not infer
    # recommendation meaning for custom question IDs or convert a five-point scale.
    question = positive_id(question_id) if question_id is not None else 1 if metric == "nps" else None
    try:
        if not all(isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) for value in (since, until)):
            raise ValueError()
        lower, upper = date.fromisoformat(since), date.fromisoformat(until)
        covering_since, covering_until = (lower - timedelta(days=1)).isoformat(), (upper + timedelta(days=1)).isoformat()
        # Validate dates, timezone and policy before accessing the profile or API.
        analysis.calculate([], metric, question, since, until, timezone, complete=True,
                           exclude_imported=not include_imported, observation=observation, denominator=denominator,
                           latest_in_period=latest_in_period)
        months = _report_months(lower, upper) if by_month else []
    except (ValueError, TypeError, OverflowError):
        raise ClientError("Report dates, timezone or metric policy are invalid.") from None
    date_field = "sendAt" if metric == "response-rate" else "endedAt"
    statuses = "completed,in-progress,abandoned,no-response" if metric == "response-rate" else "completed"
    params = [("status", statuses), ("since", covering_since), ("until", covering_until),
              ("dateFilter", date_field), ("questions", "1" if metric == "nps" else "0"), ("isImported[]", "0")]
    if include_imported:
        params.append(("isImported[]", "1"))
    if metric == "response-rate" and denominator == "attempted":
        params.append(("attempts", "1"))
    query = "/surveys?" + urlencode(params)
    directory = _new_report_directory(output_dir)
    files = {"numeric": str(directory / "numeric.json"), "calculations": str(directory / "calculations.json")}
    try:
        numeric = get(filename, query, all_pages=True, transport_fn=transport_fn, projection="numeric")
    except (ClientError, OSError, ValueError, TypeError, KeyError) as error:
        numeric = {"data": [], "pagination_complete": False, "stop_reason": "request_failed",
                   "error": "Report retrieval failed before a survey result was available."}
        numeric.update(transport.safe_error_diagnostic(error))
    api.private_write(files["numeric"], numeric)
    period = {"since": since, "until": until, "timezone": timezone}
    evidence = {"metric": metric, "period": period, "source_query": query,
                "api_covering_period": {"since": covering_since, "until": covering_until},
                "date_basis": date_field, "retrieved_at": numeric.get("retrieved_at"),
                "import_policy": "include imported surveys" if include_imported else "exclude imported surveys",
                "observation": observation if metric == "response-rate" else None,
                "denominator": denominator if metric == "response-rate" else None,
                "question_id": question, "latest_in_period": latest_in_period}
    for key in ("applied_company_ids", "company_scope_source"):
        if key in numeric:
            evidence[key] = numeric[key]
    output = {"state": "metrics_withheld", "metric": metric, "period": period,
              "as_of": numeric.get("retrieved_at"), "files": files}
    output["readout"] = _report_readout(output, analysis)
    output["source_readout"] = _report_source_readout(output, evidence, analysis)
    if (numeric.get("pagination_complete") is not True or numeric.get("error")
            or not isinstance(numeric.get("data"), list)):
        evidence.update(state="metrics_withheld", reason="retrieval_incomplete", readout=output["readout"], source_readout=output["source_readout"])
        output["reason"] = "retrieval_incomplete"
        if numeric.get("error_code") in transport.ERROR_DIAGNOSTICS:
            output["error_code"] = numeric["error_code"]
        api.private_write(files["calculations"], evidence)
        return output
    rows = numeric["data"]
    options = {"exclude_imported": not include_imported, "observation": observation, "denominator": denominator,
               "observed_as_of": numeric.get("retrieved_at") if metric == "response-rate" else None}
    try:
        overall = analysis.calculate(rows, metric, question, since, until, timezone, complete=True,
                                     latest_in_period=latest_in_period, **options)
        monthly_rows = rows
        if latest_in_period:
            winners = {str(positive_id(value)) for value in overall["selection_source_ids"]}
            monthly_rows = [row for row in rows if str(positive_id(row["id"])) in winners]
            evidence["monthly_basis"] = "Overall requested-period latest completed survey per contact, grouped by local completion month"
        else:
            evidence["monthly_basis"] = "The same retrieved cohort, selected by each exact local monthly window"
        monthly = [{"period": label, "calculation": analysis.calculate(
            monthly_rows, metric, question, start.isoformat(), end.isoformat(), timezone, complete=True,
            latest_in_period=False, **options)} for label, start, end in months]
        if any(item.get("observation_complete") is False for item in [overall] + [row["calculation"] for row in monthly]):
            evidence.update(state="metrics_withheld", reason="observation_incomplete", overall=overall, monthly=monthly)
            output["reason"] = "observation_incomplete"
        else:
            evidence.update(state="complete", overall=overall, monthly=monthly)
            output.update(state="complete", overall=_report_summary(overall, metric, latest_in_period))
            if by_month:
                output["monthly"] = [dict(period=row["period"], **_report_summary(row["calculation"], metric, latest_in_period)) for row in monthly]
                overlap = _contacts_in_multiple_months(monthly)
                output["overall"]["contacts_in_multiple_months"] = overlap
                evidence["contacts_in_multiple_months"] = overlap
            if metric == "response-rate":
                output["observation"] = ("Latest recorded responses as of retrieval" if observation == "current"
                                         else "Responses recorded by the end of each shown period" if by_month
                                         else "Responses recorded by " + until)
                output["denominator"] = ("Surveys with recorded outreach attempts" if denominator == "attempted"
                                         else "Surveys sent during the period")
            if metric == "nps":
                output["question_id"] = question
            if latest_in_period:
                output["selection"] = "Latest completed survey per contact across the requested period; monthly groups use those same selected surveys"
    except (ClientError, ValueError, TypeError, KeyError):
        evidence.update(state="metrics_withheld", reason="calculation_refused")
        output["reason"] = "calculation_refused"
    output["readout"] = _report_readout(output, analysis)
    evidence["readout"] = output["readout"]
    output["source_readout"] = _report_source_readout(output, evidence, analysis)
    evidence["source_readout"] = output["source_readout"]
    api.private_write(files["calculations"], evidence)
    return output


def bind_single_account(filename, evidence_file, transport_fn=None):
    path, profile, manifest, env = load_profile(filename)
    if env.get("approved") is not True or not env.get("identity_marker"):
        raise ClientError("Configure and verify the existing report first, then supply independent administrator evidence.")
    evidence_path = Path(evidence_file).expanduser()
    binding = private_json(evidence_path)
    candidate = dict(env, survey_owner_binding=binding)
    api.validate_survey_owner_binding(candidate)
    if env.get("survey_owner_binding") not in (None, binding):
        raise ClientError("Existing single-account binding differs; have the administrator review it before replacement.")
    env["survey_owner_binding"] = binding
    profile["last_check"] = {"verified": False, "reason": "independent-account-binding-needs-fresh-check"}
    api.private_write(path.parent / "environment.json", manifest, exclusive=False)
    api.private_write(path, profile, exclusive=False)
    return preflight(path, transport_fn=transport_fn)


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "Invalid connection arguments; use --help. No credential argument is supported.\n")


def main(argv=None):
    parser = PrivateArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("setup", help="User-only hidden key entry, generated private profile and report selection")
    create.add_argument("--kind", choices=("production", "staging"), required=True)
    create.add_argument("--origin", help="Explicit approved staging origin; production uses its fixed origin")
    create.add_argument("--account-id", required=True)
    create.add_argument("--company-ids", required=True, help="Explicit comma-separated company IDs including root")
    for target in (create, commands.add_parser("preflight", help="Check/rebind an existing private profile without reentering the key")):
        target.add_argument("--report-id")
        target.add_argument("--report-name")
    bind = commands.add_parser("bind-single-account", help="Use independently supplied administrator account/report evidence for ownerless leaf surveys")
    bind.add_argument("--evidence-file", type=Path, required=True)
    commands.add_parser("status", help="Inspect private source/configuration presence; never prints the key or calls the API")
    read = commands.add_parser("get", help="Bounded reporting-only GET using the saved explicit profile")
    read.add_argument("path")
    read.add_argument("--all-pages", action="store_true")
    read.add_argument("--projection", choices=("numeric",), help="Return survey IDs, lifecycle, numeric questions with definition labels and attempt metadata; omit contact details and answer text")
    reporting = commands.add_parser("report", help="Retrieve one numeric cohort and return a compact report with private supporting files")
    reporting.add_argument("--metric", choices=("nps", "count", "response-rate"), required=True)
    reporting.add_argument("--since", required=True)
    reporting.add_argument("--until", required=True)
    reporting.add_argument("--timezone", default="America/New_York")
    reporting.add_argument("--question-id")
    reporting.add_argument("--by-month", action="store_true")
    reporting.add_argument("--observation", choices=("current", "period-end"), default=None, help="Response-rate observation; defaults to current results")
    reporting.add_argument("--denominator", choices=("sent-status", "attempted"), default="sent-status")
    reporting.add_argument("--include-imported", action="store_true")
    reporting.add_argument("--latest-in-period", action="store_true")
    reporting.add_argument("--output-dir", type=Path, required=True)
    reporting.add_argument("--details", action="store_true", help="Include computed supporting fields and source metadata in stdout; the default returns the business readout and completion state")
    args = parser.parse_args(argv)
    try:
        if args.command == "setup":
            result = setup(args.profile, args.kind, args.account_id, args.company_ids, args.origin, args.report_id, args.report_name)
        elif args.command == "bind-single-account":
            result = bind_single_account(args.profile, args.evidence_file)
        elif args.command == "status":
            result = status(args.profile)
        elif args.command == "preflight":
            result = preflight(args.profile, args.report_id, args.report_name,
                               interactive=sys.stdin.isatty() and sys.stderr.isatty())
        elif args.command == "report":
            result = report(args.profile, args.metric, args.since, args.until, args.output_dir,
                            timezone=args.timezone, question_id=args.question_id, by_month=args.by_month,
                            observation=args.observation, denominator=args.denominator,
                            include_imported=args.include_imported, latest_in_period=args.latest_in_period)
            if not args.details:
                result = {key: result[key] for key in ("state", "readout", "reason", "error_code") if key in result}
        else:
            result = get(args.profile, args.path, args.all_pages, projection=args.projection)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 2 if (args.command in ("setup", "preflight", "bind-single-account") and result.get("state") != "verified") or result.get("error") or result.get("pagination_complete") is False or result.get("state") == "metrics_withheld" else 0
    except ClientError as error:
        result = {"error": "Connection operation refused or failed. Check the explicit profile, private terminal/file permissions, selected account/origin and report binding. No fallback, action, overwrite or retry was attempted."}
        result.update(transport.safe_error_diagnostic(error))
        print(json.dumps(result))
        return 2
    except (OSError, ValueError, TypeError, KeyError):
        print(json.dumps({"error": "Connection operation refused or failed. Check the explicit profile, private terminal/file permissions, selected account/origin and report binding. No fallback, action, overwrite or retry was attempted."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
