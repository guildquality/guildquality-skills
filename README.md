# GuildQuality Skills

Use your GuildQuality feedback with your AI assistant to understand trends, find what needs attention, and write thoughtful review replies. Connect your account for fresh feedback, or start with an approved export or a review you paste into chat.

Read [Using GuildQuality Skills](USAGE.md) to install a skill and connect your account. You can install either skill or both.

## Explore the skills

| Skill | What it helps you do | Status |
| --- | --- | --- |
| **[Analyze Feedback](skills/gq-analyze-feedback/)** | Understand trends, compare results, and find themes in customer feedback. | Available · beta |
| **[Respond to Reviews](REVIEWS.md)** | Draft replies and publish them to GuildQuality after you approve the exact text. | Available · beta |
| **Survey Customers** | Add customers and projects, and schedule their surveys. | Coming soon |
| **Manage Locations** | Add locations and manage their settings. | Planned |
| **Manage Users** | Add team members and manage their access. | Planned |

## Download and install

- **[Download Analyze Feedback](https://github.com/guildquality/guildquality-skills/releases/download/v0.2.8-beta.4/gq-analyze-feedback.zip)** · 0.2.8-beta.4
- **[Download Respond to Reviews](https://github.com/guildquality/guildquality-skills/releases/download/v0.3.0-beta.1/gq-respond-to-reviews.zip)** · 0.3.0-beta.1

Use your app's Skills screen to install each ZIP with all its files. Keep the skill folder together: it holds the instructions, reference notes, license, and Python tools the assistant needs. Select the skill in a chat, and keep customer files and saved connections in a separate private folder.

Analyze Feedback reads feedback and creates reports. Respond to Reviews drafts replies; with a working API connection, it can publish, replace, or remove a GuildQuality reply after you approve the specific change. The skills can share an existing saved connection in the same environment.

## Get started

- [Using GuildQuality Skills](USAGE.md): installation, account connection, and first questions.
- [Using Respond to Reviews](REVIEWS.md): drafting and approving replies.
- [Example questions](EXAMPLES.md): business questions to try with your own feedback.

These guides are for reading. Install the ZIPs above; the `skills/` folders show the same skill files unpacked for browsing.

The skills are available under the [MIT License](LICENSE). You may use, change, and share them under those terms.

Share only feedback your company allows you to send to your chosen AI service. Keep your API token and saved connection outside the skill folder and chat.

For help, [contact GuildQuality Support](https://help.guildquality.com/gq3/get-support-live-chat/) or email [support@guildquality.com](mailto:support@guildquality.com). For a security concern, email Support; do not post API tokens or customer feedback in a public issue.
