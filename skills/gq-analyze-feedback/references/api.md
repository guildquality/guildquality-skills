# Company API reference

Public documentation checked 2026-10-28; reporting behavior reviewed against backend source on 2026-10-31. The public [GuildQuality API documentation](https://documenter.getpostman.com/view/2124402/TVRecqCj) and the inspected backend route/controller source inform this packaged guide. It maps reporting tasks to the API and retains known behavior that affects correct analysis. Use the online documentation for additional request/response details.

## Look up capabilities when needed

Before saying a business question cannot be answered, check the relevant documentation and the selected account's available fields. Keep this lookup behind the scenes unless the user asks about the API. A documented field is a possibility, not proof that this account supplies it or that retrieval is complete.

The [public Postman page](https://documenter.getpostman.com/view/2124402/TVRecqCj) is the main online reference. It also loads [machine-readable collection JSON](https://documenter.gw.postman.com/api/collections/2124402/TVRecqCj?segregateAuth=true&versionTag=latest), verified anonymously on the date above. When a permitted web tool can fetch JSON, search its `item` entries by request name and inspect the relevant `request` method, URL, description and response examples. Entries may contain nested `item` folders. This is the published page's backing endpoint, not a guaranteed stable Postman API contract; fall back to the public page if it changes or is unavailable. Neither lookup needs the customer's GuildQuality key, a Postman key or sign-in. Do not send account data or credentials to documentation hosts, import a saved environment, or execute collection scripts or example requests as part of reading documentation.

Use this task map to choose the relevant entries:

| Business need | Documentation entries and evidence to inspect |
| --- | --- |
| Performance, trends, recurring feedback | **Get Surveys / Get Survey**: dates, statuses, question answers and available project fields; **Get Reviews / Get Review** for review feedback. |
| Locations, territories, divisions or other business groups | **Get Company Children** for related account identities; **Get Custom Fields** for field labels and possible values; survey `project.customFilters` for values actually assigned to feedback. Inspect those assignments and their business meaning before treating a group as a physical location or claiming full coverage. |
| Reuse a customer's reporting segments | **Get Reports**, then **Get Surveys** with `reportId`. Confirm actual filters and coverage before comparing saved views; a report name alone does not define a fair comparison. |
| Staff or service-role analysis | **Get Team / Get Project User Roles** plus verified assignments on survey projects. Staff names mentioned in comments do not establish responsibility. |

Reading the wider documentation does not extend the reporting helper's supported endpoints, account scope or permissions. Use the existing connection helper for customer data; never bypass a refused request because Postman lists an operation. Retain the verified caveats below when examples differ, including array-filter syntax, pagination and survey-template side effects. If an additional documented capability is not supported by the helper or cannot be checked here, identify that specific gap rather than declaring that GuildQuality has no such data. If online documentation is unavailable, use this packaged map and state any remaining uncertainty.

Production base URL: `https://www.guildquality.com/company-api/v3`. The helper requires a selected approved environment manifest, account binding, and separate private credential reference; staging does not inherit this production destination. Never infer an origin from a token or fall back after failure. Use Bearer authentication and `Accept: application/json`.

## Reads

| GET path | Filters and constraints |
| --- | --- |
| `/surveys` | `questions=1` includes answers; `attempts=1` includes recorded survey-attempt type/time; `since`, `until`, `dateFilter`, `orderBy`, `status`, `reportId`, `filterByCompanyIds` (comma-separated company IDs), `projectIds[]`, `contactIds[]`, and `isImported[]` narrow the cohort |
| `/surveys/{id}` | `questions=1`; access checked for the individual record |
| `/reviews`, `/reviews/{id}` | List supports `since`, `until`, `dateFilter`, `filterByCompanyIds` |
| `/children` | Accessible company records with `id`, `name` and `createdAt`; newer API versions can include nested `children`. Inspect the actual response. A tree alone does not establish the authenticated root, physical-location/division roles, rollup rules or complete account coverage |
| `/reports` | Non-private saved reports; excludes default All Customer/Lead Surveys |
| `/team`, `/custom-fields`, `/project-user-roles` | Reference data for interpreting and preparing requests |
| `/survey-templates` | Can initialize default templates on first access. Blocked by the reporting helper; use administrator-supplied template information instead. Never use it as a connection probe. |
| `/review-summary` | Child/affiliate summary, including question satisfaction percentages and completed-survey counts; not a universal root-account metrics endpoint |
| `/contacts/opt-in-status` | Requires `contactEmails` or a documented date filter using `since`/`until` |

Dates use **`YYYY-MM-DD`**. Survey date fields are `endedAt` (default filter), `sendAt` (default ordering), `createdAt`, `updatedAt`, and `lastActivityAt`. Review date fields are `reviewedAt` (default) and `lastActivityAt`. Confirm timezone and boundary behavior before claiming exact end-of-day coverage.

Survey `projectIds`, `contactIds`, and `isImported` filters require bracket-array query syntax. Use positive numeric IDs for `projectIds[]`/`contactIds[]`, and only `0` (not imported) or `1` (imported) for `isImported[]`. Scalar forms such as `isImported=0` can be silently ignored by the API; the helper rejects them. Do not replace this with `false`, comma-separated values, or singular `projectId`/`contactId`. For example, `isImported[]=0` selects nonimported records, while `isImported[]=0&isImported[]=1` includes both flags. PHP-indexed equivalents such as `isImported[0]=0` may appear in pagination; the helper compares their canonical cohort and rejects changed filters or endpoints. Duplicate/ambiguous typed values and returned rows contradicting the selected imported/project/contact/company filter are rejected.


`contactEmails` on `/contacts/opt-in-status` retains its documented comma-separated form, not bracket arrays. Each endpoint admits only its supported query fields. Query syntax alone does not establish completeness or an intended business cohort.

### Saved views and local analysis

A saved `reportId` can apply useful app filters, but it is not a promise that the API reproduces that view. Some saved settings override explicit fields; explicit dates can also intersect the saved range. The public report listing supplies ID/name, not a complete effective filter definition. Verify the records and any known settings before claiming an app-report match.

The inspected public survey path does not apply the app's latest-feedback-per-contact setting. Its absence is material when the user requests that view. The app can select the latest eligible response across a contact's history before applying period and other filters; keeping the newest response inside a month or quarter is a different selection. Contact IDs permit useful local grouping, but exact reconstruction requires complete authorized coverage of every record that could determine the winner. Never widen account access or claim that a period-only deduplication reproduces the app.

Other saved settings may also differ, including owner/import/completion-mode choices and rating predicates. Establish the effective choice from available authoritative context; an unknown setting is not proof that it is off. Local filtering is useful only when the required fields and complete broader group are available. Check the actual API capabilities before declaring a field unavailable. Do not use signed-in private app endpoints as a customer connector workaround.

For a broad business question, give the supported analysis with a brief, relevant scope note. For an explicitly requested view that cannot be reproduced, preserve the user's intent: explain the business difference briefly and offer an export from that view or a clearly different supported analysis. Avoid technical filter inventories in the answer.

### Attempts and minimal reporting output

`attempts=1` requests recorded attempt entries with `type` and `createdAt`; the reporting helper preserves missing versus explicitly empty lists. An attempt is evidence of outreach being attempted, not successful delivery. Include it when a response-rate definition needs attempted outreach. Verify actual returned coverage before calculating; do not infer missing attempts from an omitted field.

For a numeric reporting task, use `gq_connect.py ... get '...' --all-pages --projection numeric` to omit names, contact details, addresses, comments and action links from the returned data. It retains supported identifiers, dates, status/import flags, numeric question evidence and explicitly returned attempts. This is a data-minimization choice, not anonymization or proof of source completeness. Use only the fields needed for the task; a comment/theme analysis needs an appropriately authorized text source instead.

Survey responses may include `surveyTakeUrl`: this is a respondent action link. Do not open it as a neutral source citation or expose it unnecessarily. Cite the survey ID instead.

## Choose a bounded reporting query

For ordinary numeric questions in GuildQuality Analyze Feedback, prefer its connection helper's `report` command; it applies these query recipes and saves the actual source. The review-only skill does not include that numeric calculator. Use the lower-level GET interface for discovery or a specialized request the reporting command does not cover.

For NPS or completed-feedback counts, request `status=completed`, `dateFilter=endedAt`, the relevant date window and explicit import policy before paging. For a sent-cohort response rate, use `dateFilter=sendAt` and the eligible sent status union `status=completed,in-progress,abandoned,no-response`; include `attempts=1` when that denominator requires it. Keep the requested period for local calculations even when a bounded covering query is needed to include its timezone edges.

Apply supported filters before retrieving a larger group. Do not drop a known status or import restriction while fixing another request field. If a query is too broad, narrow it to the relevant business group and supported fields rather than repeatedly splitting the same inappropriate population. Preserve partial results and diagnose a fixed safe error code before another request; authentication or permission refusal is not a reason to try another key or bypass the connection.

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
python3 scripts/gq_connect.py --profile "$HOME/.config/guildquality/customer/connection.json" get '/surveys?questions=1&since=2026-09-01&until=2026-09-30&dateFilter=endedAt&status=completed&isImported[]=0' --all-pages
```

The helper returns `pages_fetched`, `pagination_complete`, `stop_reason`, and `data`. Check these and the process exit status. `pagination_complete: null` means no recognized paging metadata; `false` means unfinished paging. Partial data remains available when a later page fails, but is not a complete report.

Public documentation specifies 300 requests/minute per IP. Stay below that shared limit and respect actual `429`/retry guidance; do not parallelize unbounded calls. The helper does not automatically retry. For very large queries, split bounded date windows and deduplicate stable IDs; surveys reject pages above 20,000. Keep an extraction log of filters, pages, failures and coverage, never authorization headers.

## Capability boundaries

A read/write token does not imply arbitrary CRUD endpoints. The public routes do not expose generic project create/update/delete paths. Supported customer/project updates require a separately approved workflow; the reporting connection does not execute them.

Public survey/review data can support explicitly calculated analytics. It does not establish parity with every app score, eligibility rule, or native AI theme. `/review-summary` has a narrower child-summary contract and known account-shape limitations; inspect the actual response before relying on it. When required fields or filters are missing, disclose the gap instead of inventing an endpoint.

## Survey ownership and account context

Not every single-account survey response includes a company field. Missing metadata alone does not establish its owner. Normal reads continue to require returned owners within the explicit grant. An independently administrator-bound leaf account may use the documented [single-account connection](authentication.md#single-accounts-with-omitted-survey-ownership) for ownerless surveys only. The helper verifies the exact root-owned report marker and empty children afresh and labels any inference separately from server-returned fields. Do not extend that rule to reviews, hierarchy nodes or a broader account scope.
