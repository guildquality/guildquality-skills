# Connect GuildQuality privately

Use one explicit private connection profile for the selected account and environment. Install the complete skill through the client's supported Skills manager or personal skill directory; attaching a ZIP in ordinary chat does not establish persistent installation. Installation, analysis workspace, and saved connection are separate. A skill ZIP contains instructions and code, not a connection or secret store. Never put an API key in a skill, ZIP, chat, prompt, attachment, screenshot, or command argument. The Company API key can write within its server-granted scope; selecting a reporting skill does not reduce that server authority.

## Start with the actual client

Determine where this task runs, what files and network it can access, and whether it has a supported private-entry facility. Ask for only the missing nonsecret account/environment information. Preserve an existing working connection instead of starting setup again.

- **Local runtime:** the user can run the packaged setup command in their own interactive terminal. A local desktop app may not inherit exports from another terminal. Use an explicit saved profile path on each invocation.
- **Hosted ChatGPT or Claude:** laptop files, terminal variables, and local profiles are not automatically present. Verify that this exact surface exposes a supported private credential facility and permitted API networking. If it does not, explain that connection setup is unavailable there and continue permitted export analysis or drafting. Do not upload a token file, invent a private-entry form, or create servers, cloud repositories, or vault infrastructure merely to work around a missing key.
- **ChatGPT desktop with local folder access:** verify the selected folder, actual file/command tools, private profile access and permitted networking in this conversation. A Codex-backed local conversation is supported when those capabilities are present. Do not require a separate Work-mode switch or infer access from the product label alone. Hosted and local execution remain different; installing a skill does not transfer local files or credentials into a hosted session.

An `.env` file is useful only when the selected runtime already has an explicit approved loader and the user has a private way to populate it. These helpers do not scan or automatically load `.env` files. Uploading one or setting a variable on a different computer does not configure the current task. Do not search unrelated folders or credential stores for a key.

## Customer setup: one explicit profile

Resolve the installed skill directory from this client's actual skill registration. Keep the working directory in the user's private analysis workspace; do not use the installed skill folder for exports or reports. In the commands below, set `gq_skill_dir` to that verified absolute install path, for example:

```sh
gq_skill_dir="/absolute/path/to/installed/guildquality-analyze-feedback"
```

Invoke the packaged helper by that path. Use a dedicated private directory outside the installed skill and repository, with one account/environment per directory. The examples contain no key; replace account/scope/origin with explicitly approved values, never inferred from the key.

First inspect the selected profile without contacting the API:

```sh
python3 "$gq_skill_dir/scripts/gq_connect.py" --profile "$HOME/.config/guildquality/customer/connection.json" status
```

If it is not configured, prepare this command for the user to run in their **own private interactive terminal**:

```sh
python3 "$gq_skill_dir/scripts/gq_connect.py" --profile "$HOME/.config/guildquality/customer/connection.json" setup --kind production --account-id ACCOUNT_ID --company-ids ROOT_ID,CHILD_ID
```

Production explicitly uses `--kind production` and the fixed `https://www.guildquality.com` origin. A separately approved staging setup uses `--kind staging --origin EXACT_APPROVED_STAGING_ORIGIN`. Include the selected root in the explicit company-ID list. Use only approved company IDs; token reach does not itself grant task scope. Never choose production as fallback after staging fails.

Setup prompts for the key with hidden input, refuses noninteractive/piped input and refuses overwriting existing files. The agent can prepare the command but must not ask the user to paste the key in chat or capture their entry. The helper creates private `token`, `environment.json`, and profile files beside the selected profile and records a separate state-directory path. These are **plaintext files protected by ownership/permissions, not an encrypted vault**: directory 0700, files 0600 on the supported POSIX path. Keep them outside skill packaging and sharing. If they already exist, inspect status and configuration; do not overwrite or regenerate a shared key as a connection test. Windows needs an approved private injection route rather than this POSIX setup fallback.

Setup reads the account's accessible saved reports and asks the user to select an existing report in the same private terminal. If an expected marker is already independently known, supply both `--report-id ID --report-name 'Exact existing report name'`. Never invent a report name or create one just to make setup pass. Empty reports, a missing selection, or a mismatch leaves the connection unverified. The user selects account/scope; matching an actual report marker checks that binding but is not a root identity endpoint or proof of every permission.

Then check current connectivity without entering the key again:

```sh
python3 "$gq_skill_dir/scripts/gq_connect.py" --profile "$HOME/.config/guildquality/customer/connection.json" preflight
```

`preflight` reads `/reports` and verifies the exact selected ID/name. To select or correct a marker on an existing profile, use its private terminal selection or pass the two marker arguments together. HTTP 200 alone does not establish an account, marker, or usable reporting data. Inspect the result before claiming setup succeeded.

After successful preflight, use the reporting-only interface, for example:

```sh
python3 "$gq_skill_dir/scripts/gq_connect.py" --profile "$HOME/.config/guildquality/customer/connection.json" get '/surveys?questions=1&since=2026-09-01&until=2026-09-30&dateFilter=endedAt&isImported[]=0' --all-pages
```

The customer connector exposes setup, status, preflight, and GET reporting; it does not grant action execution. Read [API behavior](api.md) for cohort and pagination constraints. An approved file-only analysis does not need a live connection.

## What persistence actually proves

`status` checks local configuration and credential-file presence and shows the **last saved check**; it makes no API request. A prior verified status is not a fresh authentication check. `preflight` verifies current access. Each `gq_connect.py --profile ...` process supplies its own private token-file reference internally, so later calls do not require retyping the key or inheriting a previous shell export.

The files persist on that computer until removed. A fresh process must use the same explicit profile; a fresh conversation must also have access to that directory/runtime and recheck status/preflight. Do not claim fresh-chat or hosted persistence from a successful command in the current process. Do not attach the profile directory or key file to transfer access. A different account/environment needs its own directory/profile.

Uninstalling a skill does not delete this separate connection, and deleting the connection does not revoke the server key. Removing its dedicated files/runtime injection disconnects it locally. Rotation or revocation is a separate authorized administrator action that can affect other integrations. On authentication/scope failure, stop with secret-free diagnostics; do not try alternate keys/accounts, print server bodies/headers, or weaken permissions.

## Existing managed connections

Preserve an existing verified explicit environment configuration instead of recreating it. For an existing administrator-managed reporting configuration, the advanced `gq_api.py --manifest FILE --environment NAME` interface is also available. Use its `preflight` and `get` commands rather than recreating a working connection. Keep the manifest, private credential and saved state outside the skill and shared repositories. A configured account scope and local helper checks do not reduce the server-granted powers of the underlying API key.

This connection helper is reporting-only. Production writes are blocked by the runtime. The reporting connection does not authorize changes to customer records, outreach, or review publication.

## Single accounts with omitted survey ownership

Some single-account survey responses omit per-record company fields. The helper refuses unknown ownership by default. If this affects the connection, a GuildQuality contact or customer administrator must independently verify the account is a leaf and the selected saved report belongs to that exact root. The API key's own report list or a single-ID scope is not independent proof. The administrator supplies a private binding file containing the reviewed origin, root, report marker and evidence reference; the assistant must not invent that file or its verification.

After the existing reporting connection is configured, apply the administrator-supplied file explicitly:

```sh
python3 "$gq_skill_dir/scripts/gq_connect.py" --profile "$HOME/.config/guildquality/customer/connection.json" bind-single-account --evidence-file /private/path/admin-account-binding.json
```

This permits survey-only inference only for an exact one-root scope, fresh matching root-owned report marker and fresh complete empty children response. Each survey task checks again. The output labels the attributed account, evidence basis and affected source IDs without rewriting server fields. Keep that attribution visible in the answer. Explicit conflicting or ambiguous ownership still fails; ownerless review records do not receive this fallback. The binding is trusted administrator input, not a cryptographic identity service or an expansion of the API key's permissions.
