#!/usr/bin/env python3
"""Private, explicit-profile customer setup and reporting; no action interface.

This local interactive workflow does not supply a hosted private-entry facility.
The account connection is separate from the installed skill files.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit

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
        except (ClientError, OSError, ValueError, TypeError, KeyError, EOFError):
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


def get(filename, resource, all_pages=False, transport_fn=None):
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
        client.authorize("GET", client.url(resource))
        result = client.get(resource, all_pages=all_pages)
        return redact(result, secret)


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
        else:
            result = get(args.profile, args.path, args.all_pages)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 2 if (args.command in ("setup", "preflight", "bind-single-account") and result.get("state") != "verified") or result.get("error") or result.get("pagination_complete") is False else 0
    except (ClientError, OSError, ValueError, TypeError, KeyError):
        print(json.dumps({"error": "Connection operation refused or failed. Check the explicit profile, private terminal/file permissions, selected account/origin and report binding. No fallback, action, overwrite or retry was attempted."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
