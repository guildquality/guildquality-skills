# Get started with GuildQuality Skills

GuildQuality Skills helps your AI assistant answer questions about survey feedback, compare results, and find themes with examples from your data.

This guided pilot includes **feedback analysis only**. It does not send surveys, import customers, publish review replies, or change your GuildQuality account. Your API key can still have permission to change data, so keep it private even when you use it only for reporting.

## Before you begin

Ask your GuildQuality contact for the approved feedback-analysis package and help choosing the account and locations to include. Use your company's approved AI workspace.

For a live connection, the pilot uses a ChatGPT desktop conversation with access to a local folder and command tools, Python 3.9 or later, and permission to contact GuildQuality. The private setup process has been checked on macOS. Other operating systems and hosted chat environments may need a different approved setup; contact us before relying on them for live access.

You can also analyze an approved survey export without connecting your account or entering an API key.

## 1. Add the complete skill folder

1. Download the feedback-analysis ZIP provided by GuildQuality and unzip it.
2. Keep the whole `guildquality-analyze-feedback` folder together, including its scripts and references.
3. In the ChatGPT desktop app, start a new conversation and select the local folder containing the skill. Choose local files or this computer if the app asks where to work. The labels may vary by app version; a separate Work-mode switch is not required.
4. Ask: **“Read the GuildQuality feedback-analysis skill in this folder. Check whether this conversation can use its local files, Python tools, and GuildQuality connection.”**

Uploading `SKILL.md` as a chat attachment is not a complete installation. Installing the skill also does not connect your GuildQuality account.

## 2. Connect your account privately

A GuildQuality administrator must enable API access and provide the existing API key through your approved private process. Your GuildQuality contact will help confirm the account ID and allowed company IDs. Do not infer account access from the key alone.

Ask the assistant:

> Help me set up the packaged GuildQuality connection helper for my approved account and locations. Prepare the setup command for my private terminal. Do not ask me to put an API key in chat.

Review the account and scope before running that command in your own interactive terminal. Enter the key only at the helper's hidden prompt. Choose an existing saved report when the helper asks; do not create one just to pass setup.

**Never put the key in a chat, skill file, ZIP, screenshot, uploaded file, or command argument.**

Some accounts need an additional account binding before reporting. If the helper asks for one, request the independently checked binding file from your GuildQuality contact or account administrator. The assistant must not invent a binding or assign records to an account on its own.

The helper saves a separate private connection profile on your computer and reuses it for later reports. On the supported setup, the profile and token are plaintext files protected by local file permissions; they are not an encrypted password vault. Keep them outside the skill folder and shared folders. The assistant should remember the profile's path, not copy the key into its instructions.

If no existing report can be selected or the connection check fails, keep the current configuration and contact GuildQuality. Do not rotate a shared key or try another account just to make a test pass.

## 3. Check your first report

Start with a short period and the locations agreed for your pilot. For example:

> Summarize our completed survey feedback for last month. State the dates, time zone, locations, number of responses, exclusions, and any missing data. Show source survey IDs for examples.

Compare the result with GuildQuality using the same dates, locations, survey questions and filters. Different date definitions or rating scales can produce different results. NPS applies only to an eligible 0–10 recommendation question; a five-star or satisfaction rating should not be converted to NPS.

Then start a fresh conversation with access to the same folder and saved profile. Ask for a new connection check and report. You should not need to enter the key again. A previous saved “verified” status is not proof of a fresh API read.

## Questions to try

- **What changed?** “Compare last month's feedback with the month before. Show response counts and explain changes without assuming a cause.”
- **Where should we look first?** “Which comparable locations declined most? Show sample sizes and flag small samples, new locations and missing feedback.”
- **What are customers saying?** “What communication complaints appear in this period? Count them using a clear denominator and show representative survey IDs and exact excerpts.”
- **Are these results comparable?** “Do these survey forms use equivalent questions and scales? Explain what can be combined and what must stay separate.”
- **What is missing?** “Which locations or records are missing from this answer? Is the retrieval complete for the account and period we selected?”

## Understand the limits

An answer covers only the records and locations the connection or export actually supplies. A missing location is not automatically a zero score. Incomplete pages do not establish a company-wide total or a definitive ranking.

Large accounts may need several bounded retrievals. Your GuildQuality contact should verify the hierarchy, permitted scope and retrieval plan before a whole-company report. Installing a skill does not prove that every location or account permission is covered.

Themes produced by the assistant are its analysis of the supplied feedback. They may differ from named insights in GuildQuality. Comments can suggest issues to investigate; they do not prove what caused a score change or whether an unhappy customer's issue has been resolved.

## Update, disconnect or get help

Use only the reviewed package version provided by GuildQuality. Keep an existing working connection when updating the skill; setup and authentication are separate from installation.

Removing the skill does not remove its separate saved connection or revoke the API key. To disconnect, remove only the dedicated connection files after confirming they are not shared with another workflow. Ask your administrator before rotating or revoking a key used by other integrations.

For help, contact your GuildQuality representative. Share the package version, app and operating system, requested period and locations, and the error message with secrets and customer contact details removed. Do not send your API key or private connection files.
