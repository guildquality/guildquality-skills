# Using GuildQuality Skills

Use GuildQuality Skills in ChatGPT, Claude, or Gemini Task to understand customer feedback and write thoughtful review replies. This beta collection includes **Analyze Feedback** and **Respond to Profile Reviews**.

In ChatGPT or Claude, connect your GuildQuality account for fresh feedback and approved replies on your public **GuildQuality profile**. You can also use an export or a review you paste into chat. The Gemini Task edition works with exports and pasted reviews. Use your company's approved AI workspace and share only data your company allows.

## 1. Install GuildQuality Skills

### ChatGPT or Claude

Use the same complete collection ZIP in either app. It includes both available skills.

<p><a class="btn btn-primary btn-lg" href="https://github.com/guildquality/guildquality-skills/releases/download/v0.4.0-beta.5/guildquality-skills.zip">Download GuildQuality Skills (beta)</a></p>

Upload the ZIP without unpacking it.

**ChatGPT:** open [Plugins](https://chatgpt.com/plugins), choose **Add → Upload plugin archive**, and select the ZIP. Choose **Add plugin**, then **Install plugin**. Open GuildQuality Skills and choose **Try in chat**. Keep **GuildQuality Skills** selected as you type your question.

**Claude / Cowork:** open **Customize → Plugins → Add plugin → Upload plugin**. Select the same ZIP and choose **Upload**. The collection is enabled when installation finishes. Open GuildQuality Skills and choose **Try in chat** to begin. Keep **Analyze Feedback** selected and replace the example question with your own.

### Gemini Task

[Download the Gemini Task edition (beta)](https://github.com/guildquality/guildquality-skills/releases/download/v0.4.0-beta.5/guildquality-skills-gemini.zip) for feedback exports and review drafts. To publish a reply, copy the draft into GuildQuality or the channel you want to use.

In Gemini, open **More → Customize → Skills**, then choose **Create → Upload**. In the upload dialog, choose **files** and select the Gemini ZIP without unpacking it. Review the skill, then choose **Create**. The collection appears on your Skills page.

Start a new Gemini chat and choose **Task**. Type **@** and select **GuildQuality Skills** from the menu. Add an approved export, paste a review, or ask your business question. Keep the skill selected as you type. If Task asks for permissions the first time, review them under your company’s policy before continuing.

If Skills or Task is not available in your Gemini account, check [Google's skill requirements](https://support.google.com/gemini/answer/17094296). Use an AI workspace your company approves.

If an installation option is missing, update your app and check with your workspace administrator or GuildQuality Support. Availability depends on your plan and workspace settings. Attaching the package to a chat does not install it for future chats.

## 2. Add your GuildQuality data

Start a new chat with **GuildQuality Skills**. In ChatGPT or Claude, connect your account or upload an export. In Gemini Task, use an export or paste the review you want to answer.

### Connect your account — recommended in ChatGPT or Claude

An API connection lets the assistant read fresh feedback without downloading a new export each time. Respond to Reviews can also post replies you approve on your GuildQuality profile. Both workflows can use the same saved connection when it is available in their environment.

1. Open your [GuildQuality API settings](https://www.guildquality.com/company/manage/account/api). Sign in if asked, and check that you are in the account you want to use.
2. Turn **API** to **On**. Use the existing **API token**, or choose **Generate** if there isn't one. If you cannot change these settings, ask your GuildQuality administrator for help. Avoid **Regenerate**: it replaces the token used by any existing integrations.
3. Ask the assistant:

   > Help me connect my GuildQuality account. Check whether this chat can set up and reuse a private API connection. Walk me through setup without asking me to paste my API token into chat.

The assistant needs network access and a private place to save the token. Follow its setup instructions. If it provides a terminal command, review the account and locations before running it. Enter your token only at the hidden prompt and select an existing saved report when asked.

**Never paste your API token into chat or upload it.** Keep the saved connection outside the skill and shared folders. The saved token is not encrypted; your computer's file permissions protect it. It may allow more than reporting, so keep it private.

Connection options depend on your AI app and workspace settings. If your chat cannot connect, use an export below. You can also copy a drafted reply into GuildQuality to publish it yourself.

After setup, a fresh chat can check and reuse the saved connection. You should not need to reinstall the skill or enter the token again in that environment. Installing the collection in another app does not transfer the connection.

### Or upload an export — works in every app

Upload an approved GuildQuality export, such as a CSV or spreadsheet. To draft a reply, you can also paste the review into chat. No API token or connection setup is needed for these options.

The assistant analyzes the records in that file. Upload a new export when you want newer results. Keep local exports and reports in a private folder, separate from the installed collection.

## 3. Use the skills

Ask for what you need in your own words. You can name a skill or start with a business question. Keep asking follow-up questions in the same chat.

### Analyze Feedback

Use **GuildQuality Analyze Feedback** to understand trends, compare locations, and find themes in customer feedback. It first checks the data you have shared or connected, then uses the dates, business groups, ratings, and comments available to answer your question.

If you are not sure where to start, ask:

> What can we learn from our customer feedback?

The assistant can suggest useful questions based on your data. You can also try:

- “What happened in our business last month, and where should we focus?”
- “What are our best and worst locations right now, and why?”
- “What are customers complaining about most?”
- “Is our customer experience getting better or worse?”
- “What are our teams doing well that we should repeat elsewhere?”
- “Help me prepare a customer experience update for our leadership team.”

Choose a period covered by your data. The assistant should explain which records support the answer and point out gaps that affect the conclusion. Check those details before making decisions.

To move from a finding to a reply, ask, “Help me respond to those customers.” In ChatGPT or Claude, ask it to use **GuildQuality Respond to Reviews** if it does not choose that skill.

### Respond to Profile Reviews

Use **GuildQuality Respond to Reviews** to draft thoughtful replies from a review you paste or an approved export. In ChatGPT or Claude, a working account connection also lets you find reviews that need replies and post responses you approve on your public GuildQuality profile.

Try questions like:

- “Which reviews should we answer first? Help me draft replies.”
- “Help me reply to this unhappy customer. Keep it warm and brief.”
- “Write a thank-you reply to this positive review.”
- “Make this reply shorter and less formal.”
- “We completed the follow-up visit yesterday. Work that into the reply.”

Share only confirmed facts you want included, such as a completed service visit or an approved contact route. A review without a public reply does not tell the assistant whether your team has already helped the customer privately.

#### Review and approve before posting

In ChatGPT or Claude, with a working API connection, the assistant shows the review, any current response, and the exact proposed text before posting on your GuildQuality profile. Review the wording and approve the specific change when you are ready. Asking for a draft or editing its wording does not post it.

You can also ask to replace or remove a profile response. The assistant checks the saved result. In Gemini Task, or if your chat cannot connect, copy the draft into GuildQuality to post it yourself.

For Google or another review site, use the draft in that site's tools. For a private email, text, or call, use GuildQuality's available reply options or your email, messaging, or phone app. This skill does not send through those channels, including GuildQuality's native email. A public profile response is separate from a private reply to a survey.

## Update GuildQuality Skills

Download the latest collection ZIP again. Use **GuildQuality Skills** for ChatGPT or Claude, or the **Gemini Task edition** for Gemini.

**ChatGPT:** open GuildQuality Skills in **Plugins**. Choose **More actions → Upload new version** and select the new ZIP.

**Claude / Cowork:** use **Customize → Plugins → Add plugin → Upload plugin** to upload the same latest collection ZIP. Choose **Replace** when asked to replace GuildQuality Skills.

**Gemini:** on your Skills page, open the collection's menu and choose **Replace skill**. Choose **files** and select the latest Gemini ZIP. If the menu then shows **Activate**, choose it before starting a new chat.

Updating the collection updates both workflows. Start a new chat with GuildQuality Skills to use the latest guidance.

If you installed the earlier separate GuildQuality skills, first confirm the collection is installed and both workflows work. Then you can remove the old standalone copies from your app's Skills screen to avoid duplicates. Keep your saved API connection in its separate private folder.

## Get help

[Contact GuildQuality Support](https://help.guildquality.com/gq3/get-support-live-chat/) or email [support@guildquality.com](mailto:support@guildquality.com). Share your app, operating system, release version, question, and error message. Remove API tokens, private connection files, and customer contact details.

Use the GuildQuality app to send surveys or import customers. Codex and Claude Code are also options for people who prefer coding tools; they are not required to analyze files or draft replies.

Updating or removing the collection does not revoke your GuildQuality API token. Keep the separate saved connection in its private folder. Ask your administrator before changing a token used by other tools.
