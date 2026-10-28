# Questions to try

Start with the fictional export in `examples/synthetic-feedback.json`. No API connection is needed:

> Use the GuildQuality feedback-analysis skill with this fictional export. For September 2026, calculate NPS for recommendation question 1 on its explicit 0–10 scale. Show eligible responses and promoter/passive/detractor counts. Use America/New_York and state which records the answer covers.

With a verified account connection, try:

- “How did our customer feedback change last month? Show the eligible sample and compare with the previous complete month.”
- “Which comparable branches need a closer look? Show response counts and flag small samples or missing location mappings.”
- “Which complaints are becoming more common? Include the number of comments, the counting rule, and examples with source IDs.”
- “Did our company score change because branches scored differently, or because we heard from a different mix of branches?”
- “Compare our divisions fiscal year to date. Confirm our fiscal dates and which survey questions can be combined.”
- “What is the response rate for surveys sent last month? Explain who is in the denominator and when completed responses were observed.”

Use exact dates for a repeatable report. A score for completed surveys and a response rate for surveys sent in a period use different groups. Ask for source IDs and coverage when checking an unexpected result. See [Using GuildQuality Skills](USAGE.md) for more reporting guidance.
