# Pilot scope and limits

This pilot is for analysis and reporting. It does not authorize account administration, review publication, customer imports, survey sending or other record changes. Production mutations are blocked by the current runtime.

## Supported setup

Use a supported AI runtime with access to the complete skill folder and, for live reporting, permitted local command execution, Python 3.9+ with IANA timezone data, approved API networking and a private credential-entry route. A Codex-backed ChatGPT desktop local-folder conversation can be used when those capabilities are present. A separate Work-mode switch is not required.

A hosted ChatGPT or Claude installation alone does not provide local files, a private terminal, or a persistent connection. The current private setup helper uses POSIX ownership and file permissions. Do not assume Windows private setup or every hosted client is supported; GuildQuality will confirm the actual pilot environment. Supplied-file analysis remains available without an API key.

## Account scope and retrieval

Your API root and allowed company IDs must be explicitly configured. API company IDs are not automatically physical branches; division/region/branch mappings need a verified source. One private profile currently accepts at most 100 explicit company IDs including the root. Larger or more complex accounts need a reviewed scope and bounded reporting plan rather than an assumption that every location was retrieved.

Default retrieval budgets are 20 pages, 2,000 records and 60 seconds. The runtime's hard ceiling is 10,000 rows per bounded retrieval. A stopped query is partial. Narrow the requested period or authorized group and reconcile source IDs when combining complete subsets; never describe incomplete pages as the whole company. The calculator also limits a single invocation to 10,000 unique records and 16 MB. Preserve its limits and pool eligible counts across disjoint verified batches.

## Interpretation

Only equivalent recommendation questions on verified 0–10 scales can be pooled into the declared NPS calculation. Imported responses are excluded by default; missing answers are not zero. Small samples make rankings unstable. Counts of complaints and the share of comments containing a complaint answer different questions.

A report covers only its verified source and scope. It does not automatically establish access to every location, server-enforced regional permissions, parity with every native product metric or theme, population representativeness, or causes of a score change. Job coverage, follow-up ownership and case closure may need additional data sources.

## Private connection

The local helper stores its connection in a dedicated private directory outside the installed skill. Its token/profile files are plaintext protected by ownership and 0700/0600 permissions, not an encrypted vault. The API key retains its server-granted authority; a reporting workflow does not turn that key into a server-enforced read-only key. Uninstalling a skill does not revoke that separate key. Coordinate removal or revocation through your GuildQuality administrator.
