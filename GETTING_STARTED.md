# Get started with GuildQuality Skills

GuildQuality Skills helps your AI assistant compare customer feedback, calculate scores, and find themes with examples from your data. The current beta includes **Analyze Feedback** for reporting with an export or a private GuildQuality connection.

<p><a class="btn btn-primary btn-lg" href="https://github.com/guildquality/guildquality-skills/releases/download/v0.2.8-beta.1/guildquality-analyze-feedback.zip">Download GuildQuality Skills (beta)</a></p>

The download contains the complete skill folder. Optional checksum files on the release page verify downloads; they are not part of the installation.

## Before you begin

Use your company's approved AI workspace. For a live connection, you need a ChatGPT desktop conversation with local folder and command access, Python 3.9 or later, and permission to contact GuildQuality. Private setup has been checked on macOS; ask your GuildQuality representative about other operating systems or hosted chat environments.

You can also start with an approved survey export without connecting an account or entering an API key. The beta reads feedback and prepares reports; it does not send surveys, publish replies, or change your GuildQuality account.

## 1. Add the skill

1. Download the ZIP above and unzip it.
2. Keep the whole `guildquality-analyze-feedback` folder together, including its scripts and references.
3. In ChatGPT desktop, start a conversation and select the local folder containing the skill. Choose local files or this computer if asked. A separate Work-mode switch is not required.
4. Ask: **“Read the GuildQuality feedback-analysis skill in this folder. Check whether this conversation can use its local files, Python tools, and GuildQuality connection.”**

Use the complete folder rather than uploading `SKILL.md` alone. The repository's guides and optional checksum files do not need to be installed.

## 2. Connect your account privately

A GuildQuality administrator enables API access and provides the existing key through your approved private process. Your GuildQuality contact can help confirm the account and locations to include.

Ask the assistant:

> Help me set up the packaged GuildQuality connection helper for my approved account and locations. Prepare the setup command for my private terminal. Do not ask me to put an API key in chat.

Review the account and scope, then run the command in your own interactive terminal. Enter the key at the helper's hidden prompt and choose an existing saved report when asked.

**Keep the key out of chat, the skill folder, screenshots, uploaded files, and command arguments.** If setup asks for an account binding, get the independently checked binding file from GuildQuality or your account administrator; the assistant should not create one from assumptions.

The helper saves a separate private connection for later reports. On macOS, its profile and token are plaintext files protected by local file permissions, not an encrypted password vault. Keep them outside shared folders. The assistant needs the profile's path, not a copy of the key in its instructions.

If the check fails, keep the current configuration and contact GuildQuality before changing a key or selecting another account.

## 3. Check your first report

Start with a short period and an agreed set of locations:

> Summarize our completed survey feedback for last month. State the dates, time zone, locations, response counts, exclusions, and any missing data. Show source survey IDs for examples.

Compare the result with GuildQuality using the same dates, locations, questions, and filters. Use NPS for a verified 0–10 recommendation question; keep other rating scales separate.

Then start a fresh conversation with the same folder and saved profile. Ask for a new connection check and report. You should not need to enter the key again.

## Questions to try

- **Track change:** “Compare last month's feedback with the month before. Show response counts and explain changes without assuming a cause.”
- **Choose where to look:** “Which comparable locations declined most? Show sample sizes and flag small samples, new locations, and missing feedback.”
- **Explore comments:** “What communication complaints appear in this period? State the counting rule and show representative survey IDs and exact excerpts.”
- **Check comparisons:** “Do these survey forms use equivalent questions and scales? Explain what can be combined.”
- **Check coverage:** “Which locations and records does this answer cover? Is retrieval complete for our selected account and period?”

For larger accounts, agree the location mapping and retrieval plan with GuildQuality. Complete periods or groups make reports easier to verify; a missing location is missing coverage rather than a zero score. Themes help identify issues to investigate, while source comments provide the evidence behind them.

## Update, disconnect, or get help

Install a reviewed release and keep your existing working connection when updating the skill. Removing the skill does not remove the separate connection or revoke its API key. Confirm which connection files are dedicated to this workflow before removing them, and ask your administrator before changing a key used by other integrations.

For help, contact your GuildQuality representative with the release version, app and operating system, question, period, locations, and any error message. Remove secrets and customer contact details; keep the API key and private connection files to yourself.
