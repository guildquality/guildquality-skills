# Using Listen360 Skills

Use Listen360 Skills in ChatGPT or Claude to understand your customer feedback and write thoughtful review replies. This collection is for the **New Listen360** platform. It includes **Analyze Feedback** and **Respond to Reviews**.

Use your company's approved AI workspace and share only feedback your company allows. Connect your account where supported for fresh feedback, or upload an approved export. You can also paste a review to draft a reply.

## 1. Install Listen360 Skills

Use the same complete collection ZIP in ChatGPT or Claude. It includes both skills.

**[Download Listen360 Skills (beta)](https://github.com/guildquality/guildquality-skills/releases/download/listen360-v0.1.0-beta.7/listen360-skills.zip)**

See the [release notes](https://github.com/guildquality/guildquality-skills/releases/tag/listen360-v0.1.0-beta.7) for this version.

Upload the ZIP without unpacking it.

**ChatGPT:** open [Plugins](https://chatgpt.com/plugins), choose **Add → Upload plugin archive**, and select the ZIP. Choose **Add plugin**, then **Install plugin**. Open Listen360 Skills and choose **Try in chat**. Keep **Listen360 Skills** selected as you type your question.

**Claude / Cowork:** open **Customize → Plugins → Add plugin → Upload plugin**. Select the same ZIP and choose **Upload**. Open Listen360 Skills and choose **Try in chat**. Keep **Analyze Feedback** selected and replace the example question with your own.

If an installation option is missing, update your app and check with your workspace administrator or Listen360 Support. Availability depends on your plan and workspace settings. Attaching the ZIP to an ordinary chat does not install it for future chats.

## 2. Add your Listen360 feedback

Start a new chat with **Listen360 Skills**. Connect your account where supported, or upload an approved export. You can also paste the review you want to answer.

### Connect your account where supported

A private API connection can let the assistant read fresh feedback without downloading a new export each time. First ask:

> Help me connect my New Listen360 account. Before I change my API settings, check that this chat supports a private connection to my account. Walk me through setup without asking me to paste an API token into chat.

The assistant should confirm the supported connection method for your New Listen360 account before walking you through its API settings. Check that you are in the account you want to use. If you cannot change its settings, ask your Listen360 administrator for help.

Use the existing API token where possible. Avoid replacing a token used by another integration. Enter it only through the supported private setup, such as a hidden prompt. **Never paste or upload your API token in chat.**

This chat needs access to a private place to keep the connection and permission to use it. A connection saved on your computer is not automatically available in a web chat or another app. Ask the assistant to check that it can use the connection before relying on it.

Keep the saved connection outside the installed collection and shared folders. A saved token may be protected by your computer's file permissions rather than encryption, so keep it private.

If this chat cannot connect, use an approved export or paste a review. You can still analyze feedback and draft replies.

### Or upload an export

Upload an approved Listen360 CSV or spreadsheet. No API token is needed. The assistant analyzes the feedback you provide; upload newer feedback when you want newer results.

Keep customer files and saved reports in a private folder, separate from the installed collection.

## 3. Ask your business question

Ask for what you need in your own words. Keep follow-up questions in the same chat.

### Analyze Feedback

Use **Listen360 Analyze Feedback** to understand customer loyalty, compare locations and find themes in your feedback. It uses your report or account's chosen score when known. Otherwise, it starts with NPS (Net Promoter Score) when your feedback supports it. You can say “Show average ratings instead” or ask for another supported score.

If your feedback does not include a recommendation question, the assistant can still use other ratings and comments to help you understand the customer experience.

If you are not sure where to start, ask:

> What can we learn from our customer feedback?

You can also try:

- “What happened in our business last month, and where should we focus?”
- “What are our best and worst locations right now, and why?”
- “What are customers complaining about most?”
- “Is our customer experience getting better or worse?”
- “What are our teams doing well that we should repeat elsewhere?”
- “Help me prepare a customer experience update for our leadership team.”

Choose a period covered by your feedback. Check the scores and comments behind the findings before making decisions. If you need the exact view from a saved report, tell the assistant which report you mean and share its settings if needed.

To move from a finding to a reply, ask, “Help me respond to those customers.” You can ask it to use **Listen360 Respond to Reviews** if it does not choose that skill.

### Respond to Reviews

Use **Listen360 Respond to Reviews** to draft replies from a review you paste or an approved export.

Try questions like:

- “Help me reply to this unhappy customer.”
- “Write a thank-you reply to this positive review.”
- “Make this reply shorter and less formal.”
- “We completed the follow-up visit yesterday. Work that into the reply.”

Share only confirmed facts you want included, such as a completed service visit or an approved contact route. A review without a public reply does not tell the assistant whether your team has already helped the customer privately.

This edition **drafts replies**. Review the wording, then copy it into the appropriate Listen360 reply option, review site or email tool to send or publish it. The skill does not post, send email or text messages, or make calls. Ask Listen360 Support if you need help finding the right reply option.

## Update Listen360 Skills

Download the latest complete Listen360 Skills ZIP when a new release is available.

**ChatGPT:** open Listen360 Skills in **Plugins**. Choose **More actions → Upload new version** and select the new ZIP.

**Claude / Cowork:** use **Customize → Plugins → Add plugin → Upload plugin** to upload the latest ZIP. Choose **Replace** when asked to replace Listen360 Skills.

Start a new chat with Listen360 Skills after updating. Keep your saved connection in its separate private folder; installing or updating the collection does not transfer it between apps.

## Get help

If an answer does not look right, ask the assistant to check it against your feedback and explain the result.

For a problem, question or idea, visit [Listen360 Support](https://support.listen360.com/hc/en-us) or email [support@listen360.com](mailto:support@listen360.com). You can ask the assistant to draft a short message. Review it and send it yourself. Leave out API tokens, saved connections and customer contact details.

Use the Listen360 app to send surveys or import customers. Updating or removing the collection does not revoke an API token. Ask your administrator before changing a token used by other tools.
