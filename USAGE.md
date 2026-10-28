# Using GuildQuality Skills

GuildQuality Skills helps your AI assistant compare feedback, check scores, and find themes in customer comments. This beta includes **Analyze Feedback**. Start with a survey export or connect it to your GuildQuality account.

<p><a class="btn btn-primary btn-lg" href="https://github.com/guildquality/guildquality-skills/releases/download/v0.2.8-beta.3/guildquality-analyze-feedback.zip">Download GuildQuality Skills (beta)</a></p>

The download holds the whole skill folder. The [release page](https://github.com/guildquality/guildquality-skills/releases/tag/v0.2.8-beta.3) also offers an optional checksum to check the ZIP.

## Before you begin

Use your company's approved AI workspace. Share only feedback your company allows you to send to your chosen AI service.

A survey export needs no API key. To connect your account, the assistant also needs local files, command tools, Python 3.9 or later with time zone data, and access to the GuildQuality API. Connection setup has been checked in ChatGPT desktop on macOS. Ask GuildQuality Support about another system or a hosted chat. Installing a skill alone does not give a chat access to your computer or saved connection.

The beta reads feedback and writes reports. Use the GuildQuality app to send surveys, import customers, or publish review replies.

## 1. Install the skill

Choose your app. Keep the whole skill folder together, including its scripts, reference notes, and license.

**ChatGPT desktop:** download the ZIP above. Start a local Codex chat that can access the downloaded file, then ask:

> Install the complete GuildQuality Analyze Feedback ZIP from my Downloads folder into my personal Skills folder, `~/.agents/skills/guildquality-analyze-feedback/`. Keep all its files together. Check that it appears in Skills and tell me how to select it in a new chat. Keep my analysis work in a separate folder.

The assistant may ask to approve installing the files. Find **guildquality-analyze-feedback** in Skills and select it with **@** when starting a report. If this chat cannot install local files, contact GuildQuality Support.

**Claude:** open **Customize → Skills → + → Create skill → Upload a skill**. Upload the ZIP and enable the skill. It stays available in your account for later chats. Enable Claude's code execution and file tools if asked.

**Claude Code:** install the whole skill folder in `~/.claude/skills/guildquality-analyze-feedback/`. Ask Claude Code to help and confirm it is available in a new session. Claude's account Skills and Claude Code's local folders use different paths.

A ZIP attached to an ordinary chat is a file for that chat. Use the app's skill installation route to make it available for future work. This beta is distributed by direct download.

## 2. Choose a private place for reports

Start a normal analysis chat or project and select the installed skill. For local work, choose a separate private folder for exports and reports, such as `Documents/GuildQuality Reports`. Keep it outside the installed skill, shared folders, and Git repositories.

Ask:

> Use GuildQuality Analyze Feedback. Check that the installed skill is available. Keep my exports and reports in this private analysis folder. Tell me whether this chat can use local files, Python tools, and a saved GuildQuality connection.

If you are using an export, add the approved file and move to step 4. The [made-up sample feedback](https://github.com/guildquality/guildquality-skills/blob/main/examples/synthetic-feedback.json) is a good place to try the skill without an API key.

## 3. Connect your account privately

A GuildQuality administrator enables API access and gives you the existing API key through your company's private process. The key is a private code used to access your account. Your GuildQuality contact can confirm which account and locations to include.

Ask the assistant:

> Help me set up the GuildQuality connection for my approved account and locations. Use the installed skill's setup helper. Prepare the setup command for my private terminal. Do not ask me to put an API key in chat.

Review the account and locations. Run the command in your own terminal, such as Terminal on a Mac. Enter the key at the hidden prompt and choose an existing saved report when asked.

**Keep the key out of chat, the skill folder, screenshots, uploaded files, and command arguments.** Setup may ask for an account binding: a file that confirms which account the records belong to. Get this checked file from GuildQuality or your administrator. The assistant must not make one from guesses.

The helper saves a private connection for later reports, separate from the installed skill and your reports. On macOS, its settings and key are text files. They are not encrypted; your Mac's file permissions protect access. Keep them outside shared folders and Git repositories. The assistant needs the path to the saved connection, not a copy of the key in its instructions.

A Claude upload or hosted chat may run on another computer. It cannot use your laptop's connection just because the skill is installed. If private local setup is unavailable, use an approved export or ask Support about the right client.

The API key keeps the permissions your administrator gave it, even though this skill uses it only to read data. If a check fails, keep your current settings. Contact GuildQuality before changing a key or choosing another account.

## 4. Check your first report

Start with a clear question, a short period, and the locations you agreed to include:

> Summarize our completed survey feedback for last month. State the dates, time zone, locations, response counts, exclusions, and any missing data. Show source survey IDs for examples.

Compare the result with GuildQuality using the same dates, locations, questions, and filters. Ask for survey or review IDs so you can find the source records. Use exact dates for a report you can repeat.

Then start a fresh chat, select the installed skill, and use the same private analysis folder and saved connection. Ask for a new connection check and report. You should not need to reinstall the skill or enter the key again.

## Understand scores and themes

For Net Promoter Score (NPS), use a verified 0–10 recommendation question. Combine scores only when questions and scales match. Unanswered questions stay out of the score. Imported responses are excluded by default. If your export does not mark imported responses, get that field before asking to leave them out. Look closely at small samples before ranking locations.

Scores for completed surveys and response rates for surveys sent use different groups. For response rate, state which surveys count as sent and when completed responses were observed. Scheduled surveys are not yet sent.

For themes, ask how comments were counted: the number that mention a topic or its share of all comments. Ask for exact quotes and source survey IDs. The assistant finds themes from the feedback; they may differ from named insights in GuildQuality. Use them to choose what to explore. Comments alone do not prove a cause or show that an issue was resolved.

## Work with locations and larger reports

Have your GuildQuality contact check which accounts, locations, divisions, and regions belong in a report. API company IDs are not always physical locations. One saved connection supports up to 100 named company IDs, including the main account.

Ask whether the report includes every page for the selected account and period. For larger reports, use complete, smaller periods or groups. If a read stops early, the assistant should show what is missing and help narrow the next request. Combine complete groups that do not overlap. Use source IDs to check for duplicates, and pool the underlying response counts for an overall score.

The default read stops at 20 pages, 2,000 records, or 60 seconds. The maximum is 10,000 rows per read. The calculator accepts up to 10,000 unique records and 16 MB per report calculation. These bounds keep each report small enough to check.

Treat a missing location as missing data rather than a zero score. Check dates, filters, and survey forms before comparing groups.

## Update, disconnect, or get help

Use a reviewed release and the same installation route when updating. Keep your working connection and reports in their separate private folders. Removing the skill does not remove the saved connection or revoke its key. Check which connection files are used only by this skill before removing them. Ask your administrator before changing a key used by other tools.

For more ideas, see the [example questions](https://github.com/guildquality/guildquality-skills/blob/main/EXAMPLES.md). [Contact GuildQuality Support](https://help.guildquality.com/gq3/get-support-live-chat/) or email [support@guildquality.com](mailto:support@guildquality.com) for help. Share the release version, app, operating system, question, period, locations, and error message. Remove secrets and customer contact details. Keep the API key and private connection files to yourself. Email security concerns to Support rather than posting keys or customer feedback in a public issue.
