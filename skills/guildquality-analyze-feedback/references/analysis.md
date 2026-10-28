# Reporting and common questions

## Define the population before calculating

Record the account/location IDs, time zone, date boundaries, chosen date field, survey templates/questions, statuses, report filters, and data cutoff. “Last month” normally means the previous complete calendar month; state that assumption. Ask for fiscal boundaries when fiscal periods are requested and unknown. Do not silently compare a partial current month with a complete prior month.

Use `/children` as one source of accessible related-company IDs when needed; it does not establish a complete recursive hierarchy or physical-branch roles. Use independently verified hierarchy and role information for division/region rollups. An absent location can mean missing permission or missing data. Do not invent a root node, flatten intermediate accounts into peer locations, or combine parent aggregates with their underlying children. Select a non-overlapping cohort and deduplicate by stable record IDs. An account-wide permission claim requires evidence beyond one successful query.

Follow all pages and inspect completeness. Report selected and usable records separately. Do not treat the first 50 records, a page limit, a timeout, or inaccessible children as the complete account. If filtering must be local, retrieve the full broader cohort before computing it, or disclose the limit.

## Calculate from retrieved records

Reuse the verified complete cohort already retrieved in the current task for additional location, group, or period calculations when the same query/account scope, required fields, data cutoff, and freshness cover the new calculation. Select its actual source IDs rather than repeating an identical complete API query. Fetch again only for a changed scope/field/window, a necessary freshness check, or another concrete missing input. A partial query or stale snapshot remains partial/stale: fetch the missing pages when permitted or disclose the limit; reuse cannot establish completeness or broader account access.

When the permitted tool interface offers `calculate`, use it for bounded NPS, completed-survey counts, and sent-cohort response rate. It operates only on actually retrieved cached survey records; it accepts metric, verified `question_id` for NPS, exact `since`/`until`, timezone, optional unique retrieved `source_ids` to select a cohort, and explicit boolean `exclude_imported` (default `true`). Do not provide invented rows or seek an arbitrary shell/code tool when the client has not granted that execution capability.

The restricted calculator refuses a calculation before any survey response has actually been retrieved. A retrieved, verified complete empty query is valid evidence for a zero count or no eligible NPS answers; an untouched empty cache is not. Partial/unknown retrieval retains its incomplete flag.

In an installed local skill with permitted file execution, save the actual retrieval wrapper and run:

```sh
python3 scripts/gq_analysis.py --input retrieved.json --metric nps --question-id ID --since YYYY-MM-DD --until YYYY-MM-DD --timezone America/New_York
```

Replace the placeholders with the verified question and exact period. Imported records are excluded by default. Add `--include-imported` only when the declared metric/cohort intentionally includes them; in the restricted tool this is `exclude_imported: false`. Neither option retrieves missing records or repairs an earlier API import filter. Always state the output's actual `import_policy`. The standard-library calculator also supports `--metric count` and `--metric response-rate`. From the engineering repository root its path is `shared/scripts/gq_analysis.py`; the path above is relative to an installed skill. This calculator has no network or credential access and accepts no arbitrary code. If the permitted environment offers neither calculation route, state that execution limit rather than inventing a successful calculation.

Retain the retrieval wrapper's `pagination_complete` value. The output's `input_complete` remains false for a partial/unknown retrieval or a bare row list; arithmetic does not repair missing coverage. Even true completeness applies only to the selected source queries and granted account scope.

The candidate defaults to **excluding imported surveys** (`isImported`). Completed count/NPS use completed surveys by local `endedAt`; NPS additionally requires the verified question ID, explicit `ratingScale: "0-10"`, and an eligible integer rating. A declared historical cohort may intentionally include imported responses through the explicit policy above; disclose that choice and source provenance instead of silently changing eligibility.

For response rate, the denominator is the selected `sendAt` cohort with actual sent lifecycle states: **In Progress, Completed, Abandoned, or No Response**. Exclude **Scheduled** records even when their `sendAt` falls inside the window: a scheduled date is not proof of sending. The numerator is the completed subset of that same cohort with `endedAt` observed by the window end. Imported surveys remain excluded by default. Report the exact policy, observation cutoff, lifecycle eligibility, denominator, exclusions, and source IDs. Do not label this calculation universal native product parity or silently use it for a different business definition. The calculator does not calculate arbitrary satisfaction mappings, review scores, or themes.

## Common requests

| Request | Approach | Important distinction |
| --- | --- | --- |
| “How did we do last month?” | Completed surveys for the period, explicit answer mapping, sample sizes and comparison period | Completion cohort differs from surveys sent that month |
| “Which locations need attention?” | Comparable non-overlapping locations, eligible counts, changes and supporting comments | Low volume and missing access affect rankings |
| “Why did our score drop?” | Validate the score first, then compare question/topic distributions and representative evidence | Comments suggest explanations; they do not establish causality |
| “What do customers complain about?” | Classify relevant text, count by a declared unit, cite examples and disagreements | These are assistant-derived themes, not native GuildQuality Insights |
| “How does this quarter compare with last year?” | Match fiscal/calendar boundaries, templates, question scales, locations and cutoff | Changes in location/question mix can move totals |
| “What is our response rate?” | Define a sent cohort and observed completed responses for that cohort | Completed-in-period divided by sent-in-period is usually a different measure |
| “Show NPS or satisfaction by location” | Verify the question, scale, eligible answers and metric definition | Do not convert every rating scale into NPS or guess satisfaction thresholds |
| “Export the feedback behind that result” | Export only relevant fields and stable IDs to the agreed private destination | An export can contain personal data; avoid unnecessary names/emails |

## Metrics

For genuine 0–10 recommend questions, NPS = 100 × (promoters − detractors) / eligible answers, with 9–10 promoters, 7–8 passives, and 0–6 detractors. Exclude missing/not-applicable answers, show the eligible count, and never infer a 0–10 scale from a question label alone. Pool counts for an overall score; do not take the unweighted mean of location NPS values. For zero eligible answers, report no data, not zero.

For satisfaction or top-box metrics, use the verified question-specific positive answer mapping and denominator. If the public API does not provide the product's eligibility rules, label your calculation and explain why it may differ from the app. Distinguish percentage-point changes from relative percentage changes. Show small samples and uncertainty rather than inventing a universal minimum sample threshold.

For topic/rating association, define the unit (survey, answer, or review), allow multiple topics explicitly, and compare eligible counts for the same cohort. Do not mistake topic mentions for distinct customers or imply that correlated topics caused the rating.

## Evidence and fallback

Use survey/review IDs as provenance. Use an app link only when its actual URL is verified; do not fabricate a record URL. Label source-returned fields, calculated metrics, and inferred themes separately. If the API lacks the required field, ask for an appropriate export or explain the missing capability. Do not scrape internal endpoints or reuse browser credentials to fill the gap silently.
