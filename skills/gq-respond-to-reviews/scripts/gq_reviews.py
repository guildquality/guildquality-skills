#!/usr/bin/env python3
"""Review-only publication using an existing explicit private GuildQuality profile.

Approval records represent a human approval in the conversation; they do not
independently prove it. No customer, survey, account or team write is exposed.
"""
import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time

import gq_api as api
import gq_connect as connect
import gq_transport as transport
from gq_transport import ClientError

VERSION = "0.3.0-beta.1"
PREVIEW_SECONDS = 900
MAX_RESPONSE_CHARS = 20000
MAX_STATE_BYTES = 4_000_000


def private_state_json(filename):
    """Review snapshots can exceed the small connection-profile configuration cap."""
    path = Path(filename).expanduser()
    transport._private_stat(path.parent.lstat(), directory=True)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        transport._private_stat(info)
        if info.st_size > MAX_STATE_BYTES:
            raise ClientError("Review state exceeds the supported private-file size.")
        data = stream.read(MAX_STATE_BYTES + 1)
    if len(data) > MAX_STATE_BYTES:
        raise ClientError("Review state exceeds the supported private-file size.")
    return json.loads(data.decode("utf-8"), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))


def response_state(review):
    """The API omits response when none exists; unknown shapes are not empty."""
    if "response" not in review or review["response"] is None:
        return {"present": False, "text": None}
    value = review["response"]
    if isinstance(value, str):
        return {"present": True, "text": value}
    if isinstance(value, dict) and isinstance(value.get("comment"), str):
        return {"present": True, "text": value["comment"]}
    raise ClientError("The current review response has an unsupported shape; no change was prepared.")


def checked_request(request):
    if not isinstance(request, dict) or set(request) != {"review_id", "operation", "response"}:
        raise ClientError("A review request requires exactly review_id, operation and response.")
    target = connect.positive_id(request["review_id"])
    operation, text = request["operation"], request["response"]
    if operation not in ("publish", "replace", "clear") or not isinstance(text, str):
        raise ClientError("Use publish, replace or clear with an exact response string.")
    if (len(text) > MAX_RESPONSE_CHARS or "\x00" in text
            or operation == "clear" and text != ""
            or operation != "clear" and not text.strip()):
        raise ClientError("Publish/replace requires nonblank text; explicit clear requires an empty string.")
    return {"review_id": target, "operation": operation, "response": text}


def operation_matches(operation, current):
    if operation == "publish" and current["present"]:
        raise ClientError("This review already has a response. Show it and prepare an explicit replacement.")
    if operation in ("replace", "clear") and not current["present"]:
        raise ClientError("This review has no existing response to replace or clear.")


class ReviewClient:
    def __init__(self, filename, transport_fn=None, clock=None):
        self.filename = filename
        self.transport_fn = transport_fn
        self.clock = clock or time.time
        self._binding = None
        self._context()

    def _context(self):
        path, profile, manifest, env = connect.load_profile(self.filename)
        if env.get("approved") is not True or not env.get("identity_marker"):
            raise ClientError("The selected profile needs a verified account/report binding before review access.")
        # Reuse ordinary reporting setup without enabling the generic action mode.
        # Include scope/configuration and the actual profile path, not last-check
        # timestamps, in the immutable preview binding. No secret enters it.
        identity = {"profile": str(path), "profile_config": {k: v for k, v in profile.items() if k != "last_check"},
                    "manifest": manifest}
        binding = api.digest(identity)
        if self._binding is not None and binding != self._binding:
            raise ClientError("The selected account/profile changed; prepare and approve a new review preview.")
        self._binding = binding
        return path, profile, env

    def _state_dir(self):
        _, _, env = self._context()
        return api.private_dir(Path(env["state_dir"]) / "review-responses")

    def get(self, review_id):
        target = connect.positive_id(review_id)
        _, _, env = self._context()
        result = connect.get(self.filename, "/reviews/" + str(target), transport_fn=self.transport_fn)
        if result.get("error"):
            raise ClientError("The selected review could not be verified; no write was attempted.")
        record = result.get("data")
        if isinstance(record, dict):
            record = record.get("data", record)
        if (not isinstance(record, dict) or str(api.record_id(record)) != str(target)
                or str(api.owner(record)) not in {str(v) for v in env["allowed_company_ids"]}):
            raise ClientError("The returned review target or owner does not match the selected account grant.")
        response_state(record)
        return record

    def list(self, since=None, until=None, date_filter="reviewedAt"):
        self._context()
        if date_filter not in ("reviewedAt", "lastActivityAt"):
            raise ClientError("Choose reviewedAt or lastActivityAt for review dates.")
        params = [("dateFilter", date_filter)]
        for key, value in (("since", since), ("until", until)):
            if value is not None:
                if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                    raise ClientError("Review dates must use YYYY-MM-DD.")
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    raise ClientError("Review date is not a valid calendar day.") from None
                params.append((key, value))
        if since and until and since > until:
            raise ClientError("The review date range ends before it starts.")
        return connect.get(self.filename, "/reviews?" + api.urlencode(params), all_pages=True,
                           transport_fn=self.transport_fn)

    def preview(self, request):
        requested = checked_request(request)
        current = self.get(requested["review_id"])
        existing = response_state(current)
        operation_matches(requested["operation"], existing)
        _, _, env = self._context()
        now = self.clock()
        preview = {"schema_version": 1, "helper_version": VERSION,
                   "profile_binding": self._binding, "account_id": env["account_id"],
                   "allowed_company_ids": copy.deepcopy(env["allowed_company_ids"]),
                   "base_url": env["base_url"], "review_id": requested["review_id"],
                   "owner_id": api.owner(current), "operation": requested["operation"],
                   "destination": "GuildQuality response on review " + str(requested["review_id"]),
                   "existing_response": existing,
                   "body": {"reviewId": requested["review_id"], "response": requested["response"],
                            "responseDate": datetime.fromtimestamp(now, timezone.utc).isoformat()},
                   "before": current, "created_at": now, "expires_at": now + PREVIEW_SECONDS}
        preview["digest"] = api.digest(preview)
        if len((json.dumps(preview, indent=2, allow_nan=False) + "\n").encode()) > MAX_STATE_BYTES:
            raise ClientError("The current review is too large for a supported private preview; no change was prepared.")
        path = self._state_dir() / (preview["digest"] + ".preview.json")
        api.private_write(path, preview)
        return {"preview": preview, "preview_file": str(path), "mutation_attempted": False}

    def _validated(self, preview, allow_expired=False):
        _, _, env = self._context()
        required = {"schema_version", "helper_version", "profile_binding", "account_id", "allowed_company_ids",
                    "base_url", "review_id", "owner_id", "operation", "destination", "existing_response",
                    "body", "before", "created_at", "expires_at", "digest"}
        if not isinstance(preview, dict) or set(preview) != required:
            raise ClientError("The review preview has an unsupported shape.")
        unsigned = dict(preview)
        digest = unsigned.pop("digest")
        if (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or api.digest(unsigned) != digest or preview["schema_version"] != 1
                or preview["helper_version"] != VERSION or preview["profile_binding"] != self._binding
                or preview["account_id"] != env["account_id"] or preview["base_url"] != env["base_url"]
                or preview["allowed_company_ids"] != env["allowed_company_ids"]):
            raise ClientError("The review preview changed or belongs to a different profile/account.")
        if (type(preview["created_at"]) not in (int, float) or type(preview["expires_at"]) not in (int, float)
                or preview["expires_at"] != preview["created_at"] + PREVIEW_SECONDS
                or preview["created_at"] > self.clock() + 5
                or not allow_expired and preview["expires_at"] < self.clock()):
            raise ClientError("The review preview expired or has an invalid lifetime.")
        body = preview["body"]
        if not isinstance(body, dict) or set(body) != {"reviewId", "response", "responseDate"}:
            raise ClientError("The preview body contains unsupported API fields.")
        request = checked_request({"review_id": body["reviewId"], "operation": preview["operation"], "response": body["response"]})
        if (request["review_id"] != preview["review_id"] or not isinstance(body["responseDate"], str)
                or body["responseDate"] != datetime.fromtimestamp(preview["created_at"], timezone.utc).isoformat()
                or not isinstance(preview["before"], dict)
                or str(api.record_id(preview["before"])) != str(request["review_id"])
                or api.owner(preview["before"]) != preview["owner_id"]
                or str(preview["owner_id"]) not in {str(v) for v in env["allowed_company_ids"]}
                or response_state(preview["before"]) != preview["existing_response"]):
            raise ClientError("The review preview's request and target state disagree.")
        operation_matches(preview["operation"], preview["existing_response"])
        saved = private_state_json(self._state_dir() / (digest + ".preview.json"))
        if saved != preview:
            raise ClientError("The review preview differs from its saved private version.")
        return preview

    def _attempt_path(self, preview):
        # Exclude generated responseDate: a new timestamp must not bypass a
        # reservation for the same action against unchanged server pre-state.
        key = api.digest({"base_url": preview["base_url"], "account_id": preview["account_id"],
                          "review_id": preview["review_id"], "owner_id": preview["owner_id"],
                          "operation": preview["operation"], "response": preview["body"]["response"],
                          "before": preview["before"]})
        return self._state_dir() / (key + ".attempt.json")

    @staticmethod
    def _approval(preview, approval):
        if (not isinstance(approval, dict)
                or set(approval) != {"preview_digest", "decision", "authority", "conversation_ref"}
                or approval.get("preview_digest") != preview["digest"]
                or approval.get("decision") != "approve" or approval.get("authority") != "human"
                or not isinstance(approval.get("conversation_ref"), str)
                or not approval["conversation_ref"].strip() or len(approval["conversation_ref"]) > 2048):
            raise ClientError("Matching explicit human approval for this exact preview is required.")

    def _readback(self, preview):
        try:
            current = self.get(preview["review_id"])
            stored = response_state(current)
            matches = (stored["present"] is False if preview["operation"] == "clear"
                       else stored["present"] is True and stored["text"] == preview["body"]["response"])
            return {"state": "applied" if matches else "unknown", "stored_response_matches": matches,
                    "current_response": stored, "review_id": preview["review_id"],
                    "external_publication": "unverified", "causation": "not-established-by-state-match",
                    "retry_performed": False}
        except (ClientError, OSError, ValueError, TypeError, KeyError):
            return {"state": "unknown", "stored_response_matches": None, "review_id": preview["review_id"],
                    "reason": "Current response could not be verified; no write was retried.",
                    "external_publication": "unverified", "retry_performed": False}

    def execute(self, preview, approval):
        preview = self._validated(preview)
        self._approval(preview, approval)
        if self.get(preview["review_id"]) != preview["before"]:
            raise ClientError("The review or existing response changed. Show a fresh preview and obtain approval again.")
        path, profile, env = self._context()
        attempt_path = self._attempt_path(preview)
        attempt = {"schema_version": 1, "preview_digest": preview["digest"], "review_id": preview["review_id"],
                   "approval_ref": approval["conversation_ref"], "state": "unknown", "http_accepted": None,
                   "started_at": self.clock(), "retry_performed": False}
        try:
            api.private_write(attempt_path, attempt)
        except FileExistsError:
            raise ClientError("This review action was already reserved or attempted. Reconcile the original attempt; do not replay it.") from None
        # Reservation precedes dispatch; crashes and response loss remain safe to
        # investigate. The existing reporting manifest is never promoted to actions.
        try:
            with connect.private_reference(path, profile):
                token = api.credential_for(env)
                if self.transport_fn:
                    self.transport_fn("POST", env["base_url"] + "/review/response", copy.deepcopy(preview["body"]))
                else:
                    transport.request_json("POST", env["base_url"] + "/review/response", token,
                                           preview["body"], base_url=env["base_url"],
                                           timeout=env.get("limits", {}).get("request_timeout", 15),
                                           max_bytes=env.get("limits", {}).get("max_bytes", 1000000))
            attempt["http_accepted"] = True
        except (ClientError, OSError, ValueError, TypeError, KeyError):
            attempt["reason"] = "Dispatch failed or its receipt was lost. Readback determines the current stored state."
        attempt.update(self._readback(preview))
        api.private_write(attempt_path, attempt, exclusive=False)
        return dict(attempt, attempt_file=str(attempt_path))

    def reconcile(self, preview):
        preview = self._validated(preview, allow_expired=True)
        path = self._attempt_path(preview)
        if not path.exists():
            return {"state": "not-attempted", "review_id": preview["review_id"], "retry_performed": False}
        attempt = private_state_json(path)
        if attempt.get("preview_digest") != preview["digest"]:
            raise ClientError("Reconcile the original saved preview for this reserved action.")
        attempt.update(self._readback(preview))
        api.private_write(path, attempt, exclusive=False)
        return dict(attempt, attempt_file=str(path))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    get = commands.add_parser("get")
    get.add_argument("--review-id", required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--since")
    listing.add_argument("--until")
    listing.add_argument("--date-filter", default="reviewedAt")
    preview = commands.add_parser("preview")
    preview.add_argument("--request-file", type=Path, required=True)
    execute = commands.add_parser("execute")
    execute.add_argument("--preview-file", type=Path, required=True)
    execute.add_argument("--approval-file", type=Path, required=True)
    reconcile = commands.add_parser("reconcile")
    reconcile.add_argument("--preview-file", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        client = ReviewClient(args.profile)
        if args.command == "get":
            result = client.get(args.review_id)
        elif args.command == "list":
            result = client.list(args.since, args.until, args.date_filter)
        elif args.command == "preview":
            result = client.preview(private_state_json(args.request_file))
        elif args.command == "execute":
            result = client.execute(private_state_json(args.preview_file), private_state_json(args.approval_file))
        else:
            result = client.reconcile(private_state_json(args.preview_file))
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 2 if result.get("error") or result.get("state") == "unknown" or result.get("pagination_complete") is False else 0
    except (ClientError, OSError, ValueError, TypeError, KeyError):
        print(json.dumps({"error": "Review request refused or failed. Check the exact profile, target, current response and approval; no fallback or automatic retry occurred."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
