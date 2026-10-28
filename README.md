# GuildQuality Skills — customer pilot

Use your AI assistant to analyze GuildQuality survey and review feedback. This pilot includes the **Analyze Feedback** skill only. It supports supplied-file analysis and reporting through an explicitly configured private GuildQuality connection.

Start with [Getting Started](GETTING_STARTED.md), then try the [example questions](EXAMPLES.md). Your GuildQuality contact will help verify your first report and account scope. Use the guide supplied with your pilot for the exact supported app and setup path.

## Included

- `skills/guildquality-analyze-feedback/`: the complete skill folder, including required references and four Python runtime helpers.
- `downloads/guildquality-analyze-feedback.zip`: the same complete skill as an installable ZIP.
- `examples/synthetic-feedback.json`: a small fictional export for trying file analysis without an API key.
- `release.json` and `checksums.sha256`: version and integrity information for this pilot.

The scripts connect to the configured API, load an explicitly chosen private profile and calculate results. They are customer runtime code, not a private service. Installing a ZIP does not establish account access or give a hosted conversation access to your computer's files.

Read [pilot limits](LIMITATIONS.md) before using a report for a business decision. Keep API keys, connection profiles and customer exports out of the skill folder and repository. Never paste an API key into chat. The pilot does not publish review replies, import customers or send surveys.

This distribution is being prepared for a guided pilot and is not a public release. For access, setup help or a reporting discrepancy, contact the GuildQuality team member coordinating your pilot through your existing support channel.
