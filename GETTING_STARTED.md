# Get started with GuildQuality Skills

GuildQuality Skills helps your AI assistant compare feedback, check scores, and find themes in customer comments. This beta includes **Analyze Feedback**. Use it with a survey export or connect it to your GuildQuality account.

<p><a class="btn btn-primary btn-lg" href="https://github.com/guildquality/guildquality-skills/releases/download/v0.2.8-beta.3/guildquality-analyze-feedback.zip">Download GuildQuality Skills (beta)</a></p>

The download holds the whole skill folder. The optional checksum file checks that your download matches the release. You do not need to install it.

## Before you begin

Use your company's approved AI workspace. Share only feedback your company allows you to send to your chosen AI service.

You can start with a survey export, which needs no API key. To connect your account, the assistant also needs access to local files, command tools, Python 3.9 or later, and the GuildQuality API. This connection setup has been checked in ChatGPT desktop on macOS. Installing a skill alone does not give a chat access to your computer or saved connection.

The beta reads feedback and writes reports. It does not send surveys, publish replies, or change your account.

## 1. Install the skill once

Choose the app you use. Keep the whole skill folder together, including its scripts, reference notes, and license.

**ChatGPT desktop:** download the ZIP above. Start a local Codex chat that can access the downloaded file, then ask:

> Install the complete GuildQuality Analyze Feedback ZIP from my Downloads folder into my personal Skills folder, `~/.agents/skills/guildquality-analyze-feedback/`. Keep all its files together. Check that it appears in Skills and tell me how to select it in a new chat. Keep my analysis work in a separate folder.

The assistant may ask to approve installing the files. After installation, find **guildquality-analyze-feedback** in Skills. Select it with **@** when starting a report. If this chat cannot install local files, contact GuildQuality Support for the supported setup.

**Claude:** open **Customize → Skills → + → Create skill → Upload a skill**. Upload the ZIP above and enable the skill. It stays available in your account for later chats. Enable Claude's code execution and file tools if asked.

**Claude Code:** install the complete skill folder in your personal skills location, `~/.claude/skills/guildquality-analyze-feedback/`. Ask Claude Code to help install it and confirm it is available in a new session. Claude's account-level Skills and Claude Code's local folders use different installation paths.

A ZIP attached to an ordinary chat is a file for that chat. Use the app's skill installation route to make it available for future work. This beta is distributed by direct download.

## 2. Choose a private place for your reports

Start a normal analysis chat or project and select the installed GuildQuality skill. For local work, choose a separate private folder for your exports and reports, such as `Documents/GuildQuality Reports`. Keep it outside the installed skill, shared folders, and Git repositories.

Ask:

> Use GuildQuality Analyze Feedback. Check that the installed skill is available. Keep my exports and reports in this private analysis folder. Tell me whether this chat can use local files, Python tools, and a saved GuildQuality connection.

Your reports belong in that analysis folder. You do not need to work inside the installed skill folder. If you are using a supplied export, add the approved file and move to step 4.

## 3. Connect your account privately

A GuildQuality administrator enables API access and gives you the existing API key through your company's private process. The key is a private code used to access your account. Your GuildQuality contact can help confirm which account and locations to include.

Ask the assistant:

> Help me set up the GuildQuality connection for my approved account and locations. Use the installed skill's setup helper. Prepare the setup command for my private terminal. Do not ask me to put an API key in chat.

Review the account and locations first. Then run the command in your own terminal, such as the Terminal app on a Mac. Enter the key at the hidden prompt and choose an existing saved report when asked.

**Keep the key out of chat, the skill folder, screenshots, uploaded files, and command arguments.** Setup may ask for an account binding: a file that confirms which account the records belong to. Get this checked file from GuildQuality or your administrator. The assistant must not make one from guesses.

The helper saves a private connection for later reports, separate from the installed skill and your reports. On macOS, its settings and key are saved as text files. They are not encrypted; your Mac's file permissions protect access to them. Keep them outside shared folders and Git repositories. The assistant needs the path to the saved connection, not a copy of the key in its instructions.

A Claude upload or a hosted chat may run on a different computer from yours. It cannot use your laptop's connection just because the skill is installed. If this chat cannot use the private local setup, use an approved export or ask Support about the right client.

If the check fails, keep your current settings. Contact GuildQuality before changing a key or choosing another account.

## 4. Check your first report

Start with a short period and the locations you agreed to include:

> Summarize our completed survey feedback for last month. State the dates, time zone, locations, response counts, exclusions, and any missing data. Show source survey IDs for examples.

Compare the result with GuildQuality using the same dates, locations, questions, and filters. To calculate Net Promoter Score (NPS), use a verified 0–10 recommendation question. Keep other rating scales separate.

Then start a fresh chat, select the installed skill, and use the same private analysis folder and saved connection. Ask for a new connection check and report. You should not need to reinstall the skill or enter the key again.

## Questions to try

- **Track change:** “Compare last month's feedback with the month before. Show response counts and explain changes without assuming a cause.”
- **Choose where to look:** “Which similar locations declined most? Show sample sizes and flag small samples, new locations, and missing feedback.”
- **Explore comments:** “What complaints about communication appear in this period? Explain how you counted them and show survey IDs and exact quotes.”
- **Check comparisons:** “Do these survey forms use matching questions and scales? Explain what can be combined.”
- **Check coverage:** “Which locations and records does this answer cover? Did it include all pages for our selected account and period?”

For larger accounts, agree the location map and report plan with GuildQuality. Reports for complete periods or groups are easier to check. A missing location means missing data, rather than a zero score. Themes point to issues to explore; source comments show the evidence behind them.

## Update, disconnect, or get help

Use a reviewed release and the same installation route when updating. Keep your working connection and reports in their separate private folders. Removing the skill does not remove the saved connection or revoke its key. Check which connection files are used only by this skill before removing them. Ask your administrator before changing a key used by other tools.

[Contact GuildQuality Support](https://help.guildquality.com/gq3/get-support-live-chat/) or email [support@guildquality.com](mailto:support@guildquality.com). Share the release version, app, operating system, question, period, locations, and error message. Remove secrets and customer contact details. Keep the API key and private connection files to yourself. Email security concerns to Support rather than posting keys or customer feedback in a public issue.
