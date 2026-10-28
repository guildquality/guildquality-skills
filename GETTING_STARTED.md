# Get started with GuildQuality Skills

GuildQuality Skills helps your AI assistant compare feedback, check scores, and find themes in customer comments. This beta includes **Analyze Feedback**. Use it with a survey export or connect it to your GuildQuality account.

<p><a class="btn btn-primary btn-lg" href="https://github.com/guildquality/guildquality-skills/releases/download/v0.2.8-beta.2/guildquality-analyze-feedback.zip">Download GuildQuality Skills (beta)</a></p>

The download holds the whole skill folder. The optional checksum file checks that your download matches the release. You do not need to install it.

## Before you begin

Use your company's approved AI workspace. Share only feedback your company allows you to send to your chosen AI service.

To connect your account, you need ChatGPT desktop with access to a local folder and command tools. You also need Python 3.9 or later and permission to connect to GuildQuality. Setup has been checked on macOS. Ask GuildQuality Support about other systems or hosted chats.

You can start with a survey export instead. This does not need an API key. The beta reads feedback and writes reports. It does not send surveys, publish replies, or change your account.

## 1. Add the skill

1. Download the ZIP above and unzip it.
2. Keep the whole `guildquality-analyze-feedback` folder together, including its scripts and reference notes.
3. In ChatGPT desktop, start a chat and select the local folder that holds the skill. Choose local files or this computer if asked. You do not need a separate Work-mode switch.
4. Ask: **“Read the GuildQuality feedback-analysis skill in this folder. Check whether this chat can use its local files, Python tools, and GuildQuality connection.”**

Use the whole folder, rather than uploading `SKILL.md` alone. The guides and optional checksum files do not need to be installed.

## 2. Connect your account privately

A GuildQuality administrator enables API access and gives you the existing API key through your company's private process. The key is a private code used to access your account. Your GuildQuality contact can help confirm which account and locations to include.

Ask the assistant:

> Help me set up the GuildQuality connection for my approved account and locations. Prepare the setup command for my private terminal. Do not ask me to put an API key in chat.

Review the account and locations first. Then run the command in your own terminal, such as the Terminal app on a Mac. Enter the key at the hidden prompt and choose an existing saved report when asked.

**Keep the key out of chat, the skill folder, screenshots, uploaded files, and command arguments.** Setup may ask for an account binding: a file that confirms which account the records belong to. Get this checked file from GuildQuality or your administrator. The assistant must not make one from guesses.

The helper saves a private connection for later reports. On macOS, the connection settings and key are saved as text files. They are not encrypted; your Mac's file permissions protect access to them. Keep them outside shared folders. The assistant needs the path to the saved connection, not a copy of the key in its instructions.

If the check fails, keep your current settings. Contact GuildQuality before changing a key or choosing another account.

## 3. Check your first report

Start with a short period and the locations you agreed to include:

> Summarize our completed survey feedback for last month. State the dates, time zone, locations, response counts, exclusions, and any missing data. Show source survey IDs for examples.

Compare the result with GuildQuality using the same dates, locations, questions, and filters. To calculate Net Promoter Score (NPS), use a verified 0–10 recommendation question. Keep other rating scales separate.

Then start a fresh chat with the same folder and saved connection. Ask for a new connection check and report. You should not need to enter the key again.

## Questions to try

- **Track change:** “Compare last month's feedback with the month before. Show response counts and explain changes without assuming a cause.”
- **Choose where to look:** “Which similar locations declined most? Show sample sizes and flag small samples, new locations, and missing feedback.”
- **Explore comments:** “What complaints about communication appear in this period? Explain how you counted them and show survey IDs and exact quotes.”
- **Check comparisons:** “Do these survey forms use matching questions and scales? Explain what can be combined.”
- **Check coverage:** “Which locations and records does this answer cover? Did it include all pages for our selected account and period?”

For larger accounts, agree the location map and report plan with GuildQuality. Reports for complete periods or groups are easier to check. A missing location means missing data, rather than a zero score. Themes point to issues to explore; source comments show the evidence behind them.

## Update, disconnect, or get help

Use a reviewed release. Keep your working connection when updating the skill. Removing the skill does not remove the saved connection or revoke its key. Check which connection files are used only by this skill before removing them. Ask your administrator before changing a key used by other tools.

[Contact GuildQuality Support](https://help.guildquality.com/gq3/get-support-live-chat/) or email [support@guildquality.com](mailto:support@guildquality.com). Share the release version, app, operating system, question, period, locations, and error message. Remove secrets and customer contact details. Keep the API key and private connection files to yourself. Email security concerns to Support rather than posting keys or customer feedback in a public issue.
