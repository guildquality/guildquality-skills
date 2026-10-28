# Company API reference

Checked 2026-10-28 against the public [Postman reference](https://documenter.getpostman.com/view/2124402/TVRecqCj) and current backend route/controller source. This is a curated guide. Consult current Postman documentation before using additional fields or operations; do not send credentials to documentation URLs.

Production base URL: `https://www.guildquality.com/company-api/v3`. The helper requires a selected approved environment manifest, account binding, and separate private credential reference; staging does not inherit this production destination. Never infer an origin from a token or fall back after failure. Use Bearer authentication and `Accept: application/json`.

## Reads

| GET path | Filters and constraints |
| --- | --- |
| `/surveys` | `questions=1` includes answers; `since`, `until`, `dateFilter`, `orderBy`, `status`, `reportId`, `filterByCompanyIds` (comma-separated company IDs), `projectIds[]`, `contactIds[]`, and `isImported[]` narrow the cohort |
| `/surveys/{id}` | `questions=1`; access checked for the individual record |
| `/reviews`, `/reviews/{id}` | List supports `since`, `until`, `dateFilter`, `filterByCompanyIds` |
| `/children` | Accessible direct related-company records with `id`, `name` and `createdAt`; not a verified recursive hierarchy, root identity, physical-branch map or role/permission contract |
| `/reports` | Non-private saved reports; excludes default All Customer/Lead Surveys |
| `/team`, `/custom-fields`, `/project-user-roles` | Reference data for interpreting and preparing requests |
| `/survey-templates` | Can initialize default templates on first access. Blocked by the reporting helper; use administrator-supplied template information instead. Never use it as a connection probe. |
| `/review-summary` | Child/affiliate summary, including question satisfaction percentages and completed-survey counts; not a universal root-account metrics endpoint |
| `/contacts/opt-in-status` | Requires `contactEmails` or a documented date filter using `since`/`until` |

Dates use **`YYYY-MM-DD`**. Survey date fields are `endedAt` (default filter), `sendAt` (default ordering), `createdAt`, `updatedAt`, and `lastActivityAt`. Review date fields are `reviewedAt` (default) and `lastActivityAt`. Confirm timezone and boundary behavior before claiming exact end-of-day coverage.

Survey `projectIds`, `contactIds`, and `isImported` filters require bracket-array query syntax. Use positive numeric IDs for `projectIds[]`/`contactIds[]`, and only `0` (not imported) or `1` (imported) for `isImported[]`. Scalar forms such as `isImported=0` can be silently ignored by the API; the helper rejects them. Do not replace this with `false`, comma-separated values, or singular `projectId`/`contactId`. For example, `isImported[]=0` selects nonimported records, while `isImported[]=0&isImported[]=1` includes both flags. PHP-indexed equivalents such as `isImported[0]=0` may appear in pagination; the helper compares their canonical cohort and rejects changed filters or endpoints. Duplicate/ambiguous typed values and returned rows contradicting the selected imported/project/contact/company filter are rejected.


`contactEmails` on `/contacts/opt-in-status` retains its documented comma-separated form, not bracket arrays. Each endpoint admits only its supported query fields. Query syntax alone does not establish completeness or an intended business cohort.

Saved report filters can override explicit request fields when `reportId` is used. Check the resulting cohort before comparing it with another period or location. Do not treat a report name alone as a complete definition of its filters.

Survey responses may include `surveyTakeUrl`: this is a respondent action link. Do not open it as a neutral source citation or expose it unnecessarily. Cite the survey ID instead.

## Survey status groups and returned states

The survey-list `status` query uses **case-sensitive lowercase groups**, while each returned survey has a human-readable state. Do not copy the response label into a query.

| Query group | Returned states in that group |
| --- | --- |
| `completed` | `Completed` |
| `in-progress` | `In progress` |
| `scheduled` | `Scheduled` |
| `abandoned` | `Abandoned` |
| `no-response` | `Abandoned`, `No response` |

Comma-separated groups form a union: `status=completed,no-response` permits `Completed`, `Abandoned`, and `No response`. The groups overlap: `no-response,abandoned` still selects the two states in `no-response`; do not add group counts as if they were disjoint. Omit `status` to leave lifecycle unfiltered.

The helper rejects response-label forms such as `status=Completed`, unknown groups, explicit empty groups, and combinations containing unsupported tokens. The API can silently ignore those tokens, so an HTTP success does not prove the requested filter applied. The helper also checks returned states against the selected union and withholds a contradictory page; any earlier valid pages remain explicitly partial.

`at-risk` is not supported by this public query path: the current controller does not supply the satisfaction-index argument needed to apply that predicate. Do not substitute negative ratings for a needs-attention filter. Status groups apply to `/surveys` only; `/surveys/{id}` admits the `questions` inclusion flag, not a lifecycle filter.

## Pagination and rate limits

Survey/review lists default to 50 records per page. Omit `limit` when completeness matters: that parameter disables pagination. Follow `links.next`, validating every URL before forwarding the credential. A null next link establishes the end of that paginated query, not access to all account data. If the API returns no pagination metadata, inspect the endpoint contract; do not assume completeness.

```sh
python3 scripts/gq_connect.py --profile "$HOME/.config/guildquality/customer/connection.json" get '/reports'
python3 scripts/gq_connect.py --profile "$HOME/.config/guildquality/customer/connection.json" get '/surveys?questions=1&since=2026-09-01&until=2026-09-30&dateFilter=endedAt&isImported[]=0' --all-pages
```

The helper returns `pages_fetched`, `pagination_complete`, `stop_reason`, and `data`. Check these and the process exit status. `pagination_complete: null` means no recognized paging metadata; `false` means unfinished paging. Partial data remains available when a later page fails, but is not a complete report.

Public documentation specifies 300 requests/minute per IP. Stay below that shared limit and respect actual `429`/retry guidance; do not parallelize unbounded calls. The helper does not automatically retry. For very large queries, split bounded date windows and deduplicate stable IDs; surveys reject pages above 20,000. Keep an extraction log of filters, pages, failures and coverage, never authorization headers.

## Capability boundaries

A read/write token does not imply arbitrary CRUD endpoints. The public routes do not expose generic project create/update/delete paths. Supported customer/project updates require a separately approved workflow; the reporting connection does not execute them.

Public survey/review data can support explicitly calculated analytics. It does not establish parity with every app score, eligibility rule, or native AI theme. `/review-summary` has a narrower child-summary contract and known account-shape limitations; inspect the actual response before relying on it. When required fields or filters are missing, disclose the gap instead of inventing an endpoint.

## Survey ownership and account context

Not every single-account survey response includes a company field. Missing metadata alone does not establish its owner. Normal reads continue to require returned owners within the explicit grant. An independently administrator-bound leaf account may use the documented [single-account connection](authentication.md#single-accounts-with-omitted-survey-ownership) for ownerless surveys only. The helper verifies the exact root-owned report marker and empty children afresh and labels any inference separately from server-returned fields. Do not extend that rule to reviews, hierarchy nodes or a broader account scope.
