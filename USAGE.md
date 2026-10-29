# Using GuildQuality Skills

GuildQuality Skills helps your AI assistant compare customer feedback, check scores, and find themes in comments. This beta includes **Analyze Feedback**. Use it in ChatGPT or Claude, including their Work and Cowork features.

Use your company's approved AI workspace and share only data your company allows. You can start with a GuildQuality export. You do not need an API key to analyze a file.

<p><a class="btn btn-primary btn-lg" href="https://github.com/guildquality/guildquality-skills/releases/download/v0.2.8-beta.4/gq-analyze-feedback.zip">Download GuildQuality Skills (beta)</a></p>

## 1. Install the skill

Download the ZIP above. Use your app's Skills screen to install it with all its files.

**ChatGPT:** open [Skills](https://chatgpt.com/skills), choose **Add → Upload from your computer**, and select the ZIP. Confirm that **gq-analyze-feedback** appears under Installed. In a new chat, type **@** and select it.

**Claude / Cowork:** open **Customize → Skills → Add → Upload skill**, select the ZIP, and enable the skill. Older layouts use **+ → Create skill → Upload a skill**. Enable **Create and edit files** or **Code execution and file creation** in Settings if asked. This lets Claude analyze files; it does not mean you need Claude Code.

If the upload option is missing, update your app and check with your workspace administrator or GuildQuality Support. Availability depends on your plan and workspace settings. Attaching the ZIP to a chat does not install it for future chats.

## 2. Add your GuildQuality data

Start a new chat and ask it to use **GQ Analyze Feedback**. If your app offers **Work** or **Cowork**, use it for the analysis. In apps that combine chat and work, just describe the task.

Upload an approved GuildQuality export, such as a CSV or spreadsheet. The assistant uses the records in that file and explains any missing data that affects the answer. For local files, use a private folder for exports and reports, separate from the installed skill.

## 3. Ask a business question

Start with a period covered by your file. For example:

> Summarize our customer feedback for September.

You can ask follow-up questions in the same chat. Compare the first report with GuildQuality for the same dates and business groups before using it to make decisions.

For more ideas, see the [example questions](https://github.com/guildquality/guildquality-skills/blob/main/EXAMPLES.md).

## Optional: connect for fresh feedback

A connection lets the assistant read fresh feedback without a new export. A GuildQuality administrator must enable API access and provide the account's API key through your company's private process.

Ask the assistant:

> Help me connect my approved GuildQuality account. Check whether this chat can set up and reuse a private connection. Do not ask me to put an API key in chat.

Live access needs permitted network tools and a safe place for the saved key. Access to local files alone does not provide either. Installing the skill does not transfer a connection between your computer and a cloud chat.

Saved-connection setup and reuse have been checked in a local ChatGPT desktop session on macOS. Live API setup in ChatGPT's cloud chats and Claude/Cowork has not yet been verified for this beta. Use an export in those chats, or contact GuildQuality Support for help connecting.

For the checked local setup, the assistant prepares a command for your private terminal. Review the account and locations, run the command, enter the key at the hidden prompt, and select an existing saved report. Keep reports and connection files outside shared folders.

**Never paste your API key into chat or upload it.** The saved key is not encrypted; your computer's file permissions protect it. The key may allow more than reporting, so keep it private.

After setup, start a fresh chat and ask it to check and reuse the saved connection. You should not need to reinstall the skill or enter the key again.

## Get help

[Contact GuildQuality Support](https://help.guildquality.com/gq3/get-support-live-chat/) or email [support@guildquality.com](mailto:support@guildquality.com). Share your app, operating system, release version, question, and error message. Remove API keys, private connection files, and customer contact details.

Use the GuildQuality app to send surveys, import customers, or publish review replies. Codex and Claude Code are also options for people who prefer coding tools; they are not required for the file-analysis steps above.

Updating or removing the skill does not remove its separate connection or revoke the API key. Ask your administrator before changing a key used by other tools.
