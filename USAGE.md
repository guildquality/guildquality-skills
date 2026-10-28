# Using GuildQuality Skills

GuildQuality Skills is useful for comparing feedback over time, reviewing comparable locations, calculating recommendation scores, and finding recurring themes in customer comments. Start with a clear question, a defined group of customers, and a reporting period.

## Choose how to work

**Use an export** to ask questions about a supplied file without an API connection. The included fictional example is a good place to start.

**Connect GuildQuality** for fresh feedback from your approved account. Use a ChatGPT desktop conversation with the complete skill folder, command tools, Python 3.9+ with time zone data, and approved GuildQuality network access. Private connection setup has been checked on macOS. Ask GuildQuality to confirm the setup for another operating system or a hosted chat environment.

The beta supports analysis and reporting. Its packaged helper makes read requests only; survey sending, customer imports, and review publication belong in the GuildQuality app.

## Make reports easy to check

Ask the assistant to state the dates, time zone, included locations, survey question, response counts, and source IDs. Compare your first report with GuildQuality using those same settings.

For NPS, use a verified 0–10 recommendation question. Combine results only when questions and scales are equivalent. Imported responses are excluded by default, and unanswered questions stay out of the score. A small sample is a reason to look more closely before ranking locations.

For themes, specify whether you want the number of comments mentioning a topic or the share of all comments. Ask for representative excerpts and survey IDs. These themes are the assistant's analysis of the feedback and may differ from named insights in GuildQuality. Use them to decide what to investigate; feedback alone does not establish a cause or confirm that an issue was resolved.

## Work with locations and larger accounts

Have your GuildQuality contact verify which account IDs, physical locations, divisions, and regions belong in a report. API company IDs and physical locations are not always the same thing. One saved connection supports up to 100 explicitly configured company IDs, including the root account.

For larger reports, use complete, bounded periods or groups. Default retrieval budgets are 20 pages, 2,000 records, and 60 seconds; the maximum is 10,000 rows per retrieval. The calculator accepts up to 10,000 unique records and 16 MB per invocation. When a query stops early, the assistant should identify the missing coverage and help narrow the next request. Combine complete, non-overlapping groups using verified source IDs and pooled eligible counts.

Treat missing locations as missing coverage rather than a zero score. Check dates, filters, and survey forms before comparing groups.

## Keep the connection private

Follow [Getting Started](GETTING_STARTED.md) for private key entry and saved-connection details. The API key keeps the permissions your administrator gave it, even though this skill uses it only for reporting. Removing the skill and disconnecting the saved account are separate steps.

For help, share the release version, question, period, locations, and an error message with secrets and customer contact details removed. Contact your GuildQuality representative through your existing support channel.
