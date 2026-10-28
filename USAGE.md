# Using GuildQuality Skills

GuildQuality Skills helps your AI assistant compare customer feedback, check scores, and find themes in comments. This beta includes **Analyze Feedback**.

Start with your own data: upload an approved GuildQuality export without an API key, or connect your GuildQuality account for fresh feedback. Use your company's approved AI workspace and share only data your company allows.

<p><a class="btn btn-primary btn-lg" href="https://github.com/guildquality/guildquality-skills/releases/download/v0.2.8-beta.3/guildquality-analyze-feedback.zip">Download GuildQuality Skills (beta)</a></p>

## 1. Install the skill

Download the ZIP above and keep the whole skill folder together. Choose the instructions for your app.

**ChatGPT desktop:** start a local Codex chat that can access your download, then ask:

> Install the complete GuildQuality Analyze Feedback ZIP from my Downloads folder into my personal Skills folder, `~/.agents/skills/guildquality-analyze-feedback/`. Keep all its files together. Confirm it is available in a new chat. Keep my reports in a separate folder.

After installation, find **guildquality-analyze-feedback** in Skills and select it with **@** when starting a report.

**Claude:** open **Customize → Skills → + → Create skill → Upload a skill**. Upload the ZIP and enable the skill. Enable code execution and file tools if asked.

**Claude Code:** ask it to install the whole skill folder in `~/.claude/skills/guildquality-analyze-feedback/` and confirm it is available in a new session.

Use the app's installation steps so the skill stays available for later work. Attaching a ZIP to an ordinary chat does not install it. Contact GuildQuality Support if your app cannot complete these steps.

## 2. Add your data

Start a normal analysis chat or project and select the installed skill. For local work, choose a private folder for exports and reports, separate from the installed skill and shared folders.

### Upload your GuildQuality export

Upload a GuildQuality export your company approves for use with the AI service. The assistant uses the records in that file and explains any missing data that affects its answer. You can then move to step 3.

### Or connect your account

A GuildQuality administrator enables API access and provides your account's API key through your company's private process. Your GuildQuality contact can help confirm the account and locations to include.

This setup has been checked in ChatGPT desktop on macOS. The assistant needs local tools and access to GuildQuality. Other apps or hosted chats may need an export instead; installing the skill does not give them access to your computer.

Ask:

> Help me connect my approved GuildQuality account and locations. Check whether this chat supports the setup. Prepare the setup command for my private terminal. Do not ask me to put an API key in chat.

Review the account and locations, then run the prepared command in your own terminal, such as Terminal on a Mac. Enter the key at the hidden prompt and select an existing saved report when asked.

**Never put your API key in chat or upload it as a file.** The key may allow more than reporting, so keep it private. The helper saves the connection separately from the skill. The saved key is not encrypted; your Mac's file permissions protect it. Keep the connection outside shared folders and folders used for code.

If setup fails, keep your current settings and contact Support before changing keys or accounts.

## 3. Check your first report

Choose a short period and the locations you want to include. For an export, use dates and locations covered by the file. Ask:

> Summarize our customer feedback for the period we selected.

Compare the answer with GuildQuality for the same period and locations. If something does not match, ask the assistant to explain before acting.

For a connected account, start a fresh chat and ask it to check and reuse the saved connection. You should not need to reinstall the skill or enter the key again.

## Get help

For more ideas, see the [example questions](https://github.com/guildquality/guildquality-skills/blob/main/EXAMPLES.md). Use the GuildQuality app to send surveys, import customers, or publish review replies.

[Contact GuildQuality Support](https://help.guildquality.com/gq3/get-support-live-chat/) or email [support@guildquality.com](mailto:support@guildquality.com). Share your app, operating system, release version, question, and error message. Remove API keys, private connection files, and customer contact details.

Updating or removing the skill does not remove its separate connection or revoke the API key. Ask your administrator before changing a key used by other tools.
