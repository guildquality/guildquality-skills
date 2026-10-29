# Using GuildQuality Skills

Use GuildQuality Skills in ChatGPT or Claude to understand customer feedback and write thoughtful review replies. This beta includes **Analyze Feedback** and **Respond to Reviews**.

Connect your GuildQuality account for fresh feedback, or upload an export to get started with a file. Use your company's approved AI workspace and share only data your company allows.

Choose the skill you need, or install both. Each download is a separate skill.

<p><a class="btn btn-primary btn-lg" href="https://github.com/guildquality/guildquality-skills/releases/download/v0.2.8-beta.4/gq-analyze-feedback.zip">Download Analyze Feedback (beta)</a></p>

<p><a class="btn btn-primary btn-lg" href="https://github.com/guildquality/guildquality-skills/releases/download/v0.3.0-beta.1/gq-respond-to-reviews.zip">Download Respond to Reviews (beta)</a></p>

## 1. Install the skill

Download a ZIP above. Use your app's Skills screen to install it with all its files. Repeat for the other skill if you want both.

**ChatGPT:** open [Skills](https://chatgpt.com/skills), choose **Add → Upload from your computer**, and select the ZIP. Confirm that **gq-analyze-feedback** or **gq-respond-to-reviews** appears under Installed. In a new chat, type **@** and select it.

**Claude / Cowork:** open **Customize → Skills → Add → Upload skill**, select the ZIP, and enable the skill. Older layouts use **+ → Create skill → Upload a skill**. Enable **Create and edit files** or **Code execution and file creation** in Settings if asked. This lets Claude analyze files; it does not mean you need Claude Code.

If the upload option is missing, update your app and check with your workspace administrator or GuildQuality Support. Availability depends on your plan and workspace settings. Attaching the ZIP to a chat does not install it for future chats.

## 2. Add your GuildQuality data

Start a new chat and select **GuildQuality Analyze Feedback** or **GuildQuality Respond to Reviews**. Choose one of these two ways to add your data.

### Connect your account — recommended for fresh feedback

An API connection lets the assistant read fresh feedback without downloading a new export each time. Respond to Reviews can also publish replies you approve. Both skills can use the same saved connection in the same environment.

1. Open your [GuildQuality API settings](https://www.guildquality.com/company/manage/account/api). Sign in if asked, and check that you are in the account you want to use.
2. Turn **API** to **On**. Use the existing **API token**, or choose **Generate** if there isn't one. If you cannot change these settings, ask your GuildQuality administrator for help. Avoid **Regenerate**: it replaces the token used by any existing integrations.
3. Ask the assistant:

   > Help me connect my GuildQuality account. Check whether this chat can set up and reuse a private API connection. Walk me through setup without asking me to paste my API token into chat.

The assistant needs network access and a private place to save the token. Follow its setup instructions. If it provides a terminal command, review the account and locations before running it. Enter your token only at the hidden prompt and select an existing saved report when asked.

**Never paste your API token into chat or upload it.** Keep the saved connection outside the skill and shared folders. The saved token is not encrypted; your computer's file permissions protect it. It may allow more than reporting, so keep it private.

Connection options depend on your AI app and workspace settings. If your chat cannot connect, use an export below. You can also copy a drafted reply into GuildQuality to publish it yourself.

After setup, a fresh chat can check and reuse the saved connection. You should not need to reinstall the skill or enter the token again in that environment. Installing the skill elsewhere does not transfer the connection.

### Or upload an export — a simple way to start

Upload an approved GuildQuality export, such as a CSV or spreadsheet. To draft a reply, you can also paste the review into chat. No API token or connection setup is needed for these options.

The assistant analyzes the records in that file. Upload a new export when you want newer results. Keep local exports and reports in a private folder, separate from the installed skill.

## 3. Ask for what you need

With **Analyze Feedback**, choose a period covered by your data:

> What happened in our business last month, and where should we focus?

Ask follow-up questions in the same chat. Check the dates and business groups used in the report before making decisions. For more ideas, see the [example questions](https://github.com/guildquality/guildquality-skills/blob/main/EXAMPLES.md).

With **Respond to Reviews**, try:

> Which reviews should we answer first? Help me draft replies.

Or paste a review and ask:

> Help me reply to this unhappy customer. Keep it warm and brief.

Share confirmed facts you want included, such as a completed service visit. You can ask for a shorter reply, a different tone, or another language.

### Review and approve before publishing

With a working API connection, the assistant shows the review, any current reply, and the exact proposed text before publishing. Approve the specific change when you are ready. Asking for a draft or changing its wording does not publish it.

You can also ask to replace or remove a reply. The assistant checks the saved result. If your chat cannot connect, copy the draft into GuildQuality yourself. Replies for Google or other sites must be posted through those sites' own tools.

For more detail, read [Using GuildQuality Respond to Reviews](https://github.com/guildquality/guildquality-skills/blob/main/REVIEWS.md).

## Get help

[Contact GuildQuality Support](https://help.guildquality.com/gq3/get-support-live-chat/) or email [support@guildquality.com](mailto:support@guildquality.com). Share your app, operating system, release version, question, and error message. Remove API tokens, private connection files, and customer contact details.

Use the GuildQuality app to send surveys or import customers. Codex and Claude Code are also options for people who prefer coding tools; they are not required to analyze files or draft replies.

Updating or removing the skill does not remove its separate connection or revoke the API token. Ask your administrator before changing a token used by other tools.
