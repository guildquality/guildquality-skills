# Using GuildQuality Skills

Use GuildQuality Skills to compare feedback over time, check results across similar locations, and find common themes in comments. Start with a clear question, a group of customers, and a time period.

## Choose how to work

**Use an export** to ask about a supplied file without an API connection. The made-up example is a good place to start.

**Connect GuildQuality** to read fresh feedback from your approved account. Use the installed skill in ChatGPT desktop with local files, command tools, Python 3.9+ with time zone data, and permission to connect. Private setup has been checked on macOS. Ask GuildQuality to confirm the setup for another system or a hosted chat.

Install the skill once using [Getting Started](GETTING_STARTED.md), then select it in your normal analysis chat or project. Keep local exports and reports in a separate private folder outside the installed skill and Git repositories. A hosted chat does not gain access to your laptop's saved connection through installation.

The beta reads feedback and writes reports. Use the GuildQuality app to send surveys, import customers, or publish review replies. Share only feedback your company allows you to send to your chosen AI service.

## Make reports easy to check

Ask the assistant to state the dates, time zone, locations, survey question, and response counts. Ask for survey or review IDs so you can find the source records. Compare your first report with GuildQuality using the same settings.

For Net Promoter Score (NPS), use a verified 0–10 recommendation question. Combine scores only when questions and scales match. Imported responses are excluded by default. If your export does not mark imported responses, get that field before asking to leave them out. Unanswered questions stay out of the score. Look closely at small samples before ranking locations.

For themes, ask for the number of comments that mention a topic or its share of all comments. Ask for exact quotes and survey IDs. The assistant finds these themes from the feedback. They may differ from named insights in GuildQuality. Use them to choose what to explore. Comments alone do not prove a cause or show that an issue was resolved.

## Work with locations and larger accounts

Have your GuildQuality contact check which accounts, locations, divisions, and regions belong in a report. API company IDs are not always the same as physical locations. One saved connection supports up to 100 named company IDs, including the main account.

For larger reports, ask for complete, smaller periods or groups. If a query stops early, the assistant should show what is missing and help narrow the next request. Combine complete groups that do not overlap. Use source IDs to check for duplicate records, and combine the underlying response counts for an overall score.

The default read stops at 20 pages, 2,000 records, or 60 seconds. The maximum is 10,000 rows per read. The calculator accepts up to 10,000 unique records and 16 MB per report calculation. These bounds help keep each report small enough to check.

Treat a missing location as missing data rather than a zero score. Check dates, filters, and survey forms before comparing groups.

## Keep the connection private

Follow [Getting Started](GETTING_STARTED.md) to enter your key and save the connection privately. The API key keeps the permissions your administrator gave it, even though this skill uses it only to read data. Removing the skill and disconnecting the account are separate steps.

For help, share the release version, question, period, locations, and error message. Remove secrets and customer contact details. [Contact GuildQuality Support](https://help.guildquality.com/gq3/get-support-live-chat/) or email [support@guildquality.com](mailto:support@guildquality.com).
