# Using GuildQuality Skills

GuildQuality Skills helps your AI assistant compare customer feedback, check scores, and find themes in comments. This beta includes **Analyze Feedback**. Use it in ChatGPT or Claude, including their Work and Cowork features.

Connect your GuildQuality account for fresh feedback, or upload an export to get started with a file. Use your company's approved AI workspace and share only data your company allows.

<p><a class="btn btn-primary btn-lg" href="https://github.com/guildquality/guildquality-skills/releases/download/v0.2.8-beta.4/gq-analyze-feedback.zip">Download GuildQuality Skills (beta)</a></p>

## 1. Install the skill

Download the ZIP above. Use your app's Skills screen to install it with all its files.

**ChatGPT:** open [Skills](https://chatgpt.com/skills), choose **Add → Upload from your computer**, and select the ZIP. Confirm that **gq-analyze-feedback** appears under Installed. In a new chat, type **@** and select it.

**Claude / Cowork:** open **Customize → Skills → Add → Upload skill**, select the ZIP, and enable the skill. Older layouts use **+ → Create skill → Upload a skill**. Enable **Create and edit files** or **Code execution and file creation** in Settings if asked. This lets Claude analyze files; it does not mean you need Claude Code.

If the upload option is missing, update your app and check with your workspace administrator or GuildQuality Support. Availability depends on your plan and workspace settings. Attaching the ZIP to a chat does not install it for future chats.

## 2. Add your GuildQuality data

Start a new chat and ask it to use **GuildQuality Analyze Feedback**. If your app offers **Work** or **Cowork**, use it for the analysis. Choose one of these two ways to add your data.

### Connect your account — recommended for fresh feedback

An API connection lets the assistant read fresh feedback without downloading a new export each time.

1. Open your [GuildQuality API settings](https://www.guildquality.com/company/manage/account/api). Sign in if asked, and check that you are in the account you want to analyze.
2. Turn **API** to **On**. Use the existing **API token**, or choose **Generate** if there isn't one. If you cannot change these settings, ask your GuildQuality administrator for help. Avoid **Regenerate**: it replaces the token used by any existing integrations.
3. Ask the assistant:

   > Help me connect my GuildQuality account. Check whether this chat can set up and reuse a private API connection. Walk me through setup without asking me to paste my API token into chat.

The assistant needs network tools and a private place to save the token. For the checked local setup, it prepares a command for your private terminal. Review the account and locations, run the command, copy your token from API settings into the hidden prompt, and select an existing saved report.

**Never paste your API token into chat or upload it.** Keep the saved connection outside the skill and shared folders. The saved token is not encrypted; your computer's file permissions protect it. It may allow more than reporting, so keep it private.

Saved-connection setup and reuse have been checked in a local ChatGPT desktop session on macOS. API setup in ChatGPT's cloud chats and Claude/Cowork is still being verified for this beta. If your chat cannot connect, use an export below or contact GuildQuality Support.

After setup, a fresh chat can check and reuse the saved connection. You should not need to reinstall the skill or enter the token again in that environment. Installing the skill elsewhere does not transfer the connection.

### Or upload an export — a simple way to start

Upload an approved GuildQuality export, such as a CSV or spreadsheet. No API token or connection setup is needed. This is also a useful option if you have trouble connecting.

The assistant analyzes the records in that file. Upload a new export when you want newer results. Keep local exports and reports in a private folder, separate from the installed skill.

## 3. Ask a business question

Choose a period covered by your data. For example:

> Summarize our customer feedback for September.

You can ask follow-up questions in the same chat. Compare the first report with GuildQuality for the same dates and business groups before using it to make decisions.

For more ideas, see the [example questions](https://github.com/guildquality/guildquality-skills/blob/main/EXAMPLES.md).

## Get help

[Contact GuildQuality Support](https://help.guildquality.com/gq3/get-support-live-chat/) or email [support@guildquality.com](mailto:support@guildquality.com). Share your app, operating system, release version, question, and error message. Remove API tokens, private connection files, and customer contact details.

Use the GuildQuality app to send surveys, import customers, or publish review replies. Codex and Claude Code are also options for people who prefer coding tools; they are not required for the file-analysis steps above.

Updating or removing the skill does not remove its separate connection or revoke the API token. Ask your administrator before changing a token used by other tools.
