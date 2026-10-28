# GuildQuality Skills

Analyze GuildQuality customer feedback with your AI assistant. Compare periods and locations, calculate scores, and explore customer comments with examples from your data.

**Current release: 0.2.8-beta.1.** This beta includes the **Analyze Feedback** skill for reporting with a survey export or a private GuildQuality API connection.

**[Download GuildQuality Skills (beta)](https://github.com/guildquality/guildquality-skills/releases/download/v0.2.8-beta.1/guildquality-analyze-feedback.zip)**

Follow [Getting Started](GETTING_STARTED.md) to add the skill and connect your account. Then try the [example questions](EXAMPLES.md) and read [Using GuildQuality Skills](USAGE.md) for guidance on comparisons, larger accounts, and reliable reports.

## What to install

Download and unzip **`guildquality-analyze-feedback.zip`**, then keep the complete skill folder together. It contains the instructions, references, and Python helpers the assistant needs. The beta reads feedback and prepares reports; it does not change your account or send messages.

The other files in this repository support setup and use:

- `GETTING_STARTED.md`, `EXAMPLES.md`, and `USAGE.md`: guides to read, not files to install.
- `examples/synthetic-feedback.json`: fictional feedback for trying a report without an API key.
- `skills/guildquality-analyze-feedback/`: the same skill files unpacked for browsing.
- `release.json` and `checksums.sha256`: version information and optional download verification. The checksum file is not part of the installed skill.

Use your company's approved AI workspace. Keep your API key and saved connection outside the skill folder and chat. Your GuildQuality representative can help with setup, account scope, or a report you want to check.
