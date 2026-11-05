# iOS Shortcuts for ORGANVM Dashboard

Four shortcuts for quick system interaction from iPhone. Each uses `GET` → parse JSON → display.

**Base URL:** `https://dash.ivixivi.xyz/api/v1`
**Auth header:** `X-API-Key: <your-key>` (retrieve from Keychain: `security find-generic-password -s "organvm-api-key" -w`)

---

## 1. System Pulse

Quick system health check — shows repo counts, CI coverage, omega progress.

### Steps
1. **Get Contents of URL**
   - URL: `https://dash.ivixivi.xyz/api/v1/status`
   - Method: GET
   - Headers: `X-API-Key` → `<your-key>`
2. **Get Dictionary Value** for key `total_repos` → save as `Total`
3. **Get Dictionary Value** for key `active_repos` → save as `Active`
4. **Get Dictionary Value** for key `ci_coverage` → save as `CI`
5. **Show Result**: `ORGANVM: {Active}/{Total} active repos, CI: {CI}`

---

## 2. Omega Scorecard

Shows the 17-criterion omega maturity checklist.

### Steps
1. **Get Contents of URL**
   - URL: `https://dash.ivixivi.xyz/api/v1/omega`
   - Method: GET
   - Headers: `X-API-Key` → `<your-key>`
2. **Get Dictionary Value** for key `met_count` → save as `Met`
3. **Get Dictionary Value** for key `total_criteria` → save as `Total`
4. **Get Dictionary Value** for key `criteria` → save as `Criteria`
5. **Repeat with each** item in `Criteria`:
   - **Get Dictionary Value** for key `name` → `Name`
   - **Get Dictionary Value** for key `met` → `Status`
   - **If** `Status` is true: append `✅ {Name}` to `Output`
   - **Otherwise**: append `⬜ {Name}` to `Output`
6. **Show Result**: `Omega: {Met}/{Total}\n{Output}`

---

## 3. Registry Search

Search repos by name pattern.

### Steps
1. **Ask for Input** — text, prompt: "Search repos:"
2. **Get Contents of URL**
   - URL: `https://dash.ivixivi.xyz/api/v1/registry?name_pattern={input}`
   - Method: GET
   - Headers: `X-API-Key` → `<your-key>`
3. **Get Dictionary Value** for key `repos` → save as `Repos`
4. **Get Dictionary Value** for key `total` → save as `Count`
5. **Repeat with each** item in `Repos`:
   - **Get Dictionary Value** for keys `name`, `organ`, `promotion_status`
   - Append `{organ}/{name} [{promotion_status}]` to `Output`
6. **Show Result**: `{Count} repos found:\n{Output}`

---

## 4. Governance Audit

Run the governance audit and show warnings.

### Steps
1. **Get Contents of URL**
   - URL: `https://dash.ivixivi.xyz/api/v1/governance/audit`
   - Method: GET
   - Headers: `X-API-Key` → `<your-key>`
2. **Get Dictionary Value** for key `summary` → save as `Summary`
3. **Get Dictionary Value** for key `warnings` → save as `Warnings`
4. **Get Count** of `Warnings` → save as `WarnCount`
5. **If** `WarnCount` > 0:
   - **Repeat with each** warning: append `⚠️ {warning}` to `Output`
   - **Show Result**: `Governance: {WarnCount} warnings\n{Output}`
6. **Otherwise**: **Show Result**: `Governance: All clear ✅`

---

## Tips

- **Widget**: Add any shortcut to your Home Screen as a widget for one-tap access
- **Siri**: "Hey Siri, System Pulse" works once shortcuts are named
- **Automation**: Use Shortcuts Automations to run "System Pulse" at 9am daily
- **Share Sheet**: Add "Registry Search" to the share sheet for quick lookups
