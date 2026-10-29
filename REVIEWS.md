# Using GuildQuality Respond to Reviews

Draft thoughtful review replies in ChatGPT or Claude. Connect your account to find reviews and post approved responses on your **GuildQuality profile**, or start with a review you paste or upload for a draft.

## Install the skill

**[Download Respond to Reviews (beta)](https://github.com/guildquality/guildquality-skills/releases/download/v0.3.0-beta.2/gq-respond-to-reviews.zip)**

Install the complete `gq-respond-to-reviews.zip` using your app's Skills screen. In ChatGPT, choose **Add → Upload from your computer**. In Claude, choose **Customize → Skills → Add → Upload skill** and enable it.

Already installed? Use the new ZIP to update the skill in your app's Skills screen. Update Analyze Feedback too if you use both.

Start a new chat and select the skill, or ask to use **GuildQuality Respond to Reviews**. Keep customer files and saved connections in a separate private folder.

## Connect to find GuildQuality reviews

Use the account connection from [Using GuildQuality Skills](USAGE.md#2-add-your-guildquality-data). An existing saved connection can serve both Analyze Feedback and Respond to Reviews in the same environment. Never paste an API token into chat or upload it.

Ask the assistant to find a review or show reviews that need replies. You can also move from an analysis to a draft by asking, “Help me respond to those customers.” Select Respond to Reviews if your app does not choose it.

## Draft and revise a reply

Paste a review or upload an approved export and describe what you want. For example:

> Help me reply to this unhappy customer. Keep it warm and brief.

You can ask for a shorter reply, a different tone, or another language. Share confirmed facts you want included, such as a completed service visit or an approved contact route. You do not need an API token to draft a reply.

For several reviews, ask:

> Which reviews should we answer first? Draft replies for the ones we haven't answered.

A missing public response does not tell the assistant whether your team has helped the customer privately. Include that context when it matters.

## Choose where the reply goes

**GuildQuality profile:** with a working API connection, the skill can post, replace, or remove a response on a GuildQuality review. Before posting, it shows the review, any current response, and the exact proposed text. Approve the specific change when you are ready. Asking for a draft or editing its wording does not post it. The assistant checks the saved result; if the result is uncertain, it checks the current state before proposing another action.

**Google or another review site:** the skill can draft the wording. Post it through that site's own tools.

**Private email, text, or phone:** the skill can help prepare wording. Use GuildQuality's available reply options or your email, messaging, or phone app to contact the customer. The skill does not send private messages, use GuildQuality's native email, or place calls. Opening another app does not mean a message was sent or a call was made.

The public profile response is separate from a private reply to a survey. If the destination is unclear from the conversation, the assistant should confirm where you want the reply to go.

Connection options depend on your AI app and workspace settings. If your chat cannot connect, copy the draft into GuildQuality to post it yourself.

## Get help

[Contact GuildQuality Support](https://help.guildquality.com/gq3/get-support-live-chat/) or email [support@guildquality.com](mailto:support@guildquality.com). Share your question, app, and error message. Remove API tokens, connection files, and customer contact details.
