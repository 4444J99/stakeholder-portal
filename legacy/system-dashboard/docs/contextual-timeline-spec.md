# Contextual Timeline Specification

## Purpose
Capture the "timeline-to-finishline" system you described: a completion meter that reshapes itself depending on how deeply the reader has zoomed into the meta-ORGANVM system, from the enterprise level down to the smallest feature atom. This doc sits in `system-dashboard/docs/` because the dashboard already renders the alpha→omega meter, and the spec reminds implementers what data flows and UI states are expected as we move between contexts.

## Contextual layers
1. **Enterprise Scope (macro)** – the system dashboard home page (`/progress/`) must show a single progress meter and gating summary for the entire workspace, derived from all repos (see `system-dashboard/templates/progress.html`).
2. **Organ Scope** – when the user selects an organism card, the meter re-skins itself to represent that organ's aggregate progress (promo-ready repos, stale counts, gate pass rate). The organ card already contains the organ-level % and gate strips pulled from `evaluate_all_for_dashboard` in `system-dashboard/src/dashboard/routes/progress.py`.
3. **Repo Scope** – clicking a repo drills into `/progress/repo/{name}`, where the UI renders the repo’s own gate strip, implementation metadata, and the meter becomes that repo’s completion %, as shown in `progress_detail.html`.
4. **Feature Atom Scope** – future requirements (or existing expansions) should allow the meter to represent smaller constructs (for example, a particular gate, feature flag, or atom within a repo). Define data contracts so a single gate object can be selected, and the UI can re-render the same progress bar for that atom.

## Data model and APIs
- `evaluate_all_for_dashboard()` currently returns per-repo gate lists, percentages, promo readiness, etc. Extend it to return a `context_hierarchy` array (e.g., `["SYSTEM", "ORGAN-IV", "repo-x"]`) or similar metadata that the UI can use when selecting nested levels.
- Add optional `atoms` field to each gate to describe sub-elements (name, status, related metric). This lets future UI expansions render atom-level meters.
- `/progress/api` should expose the hierarchy metadata so external clients (AI assistants, other dashboards) can render the same nesting effect.
- Define canonical labels for contexts (SYSTEM, ORGAN, REPO, ATOM) and ensure the UI reads them when picking the fill color, tooltip copy, and descriptive heading.

## UI behavior
- System view: single progress bar with summary metrics (`total_repos`, `sys_pct`, gate rate bars). This is the macro meter that updates whenever the registry changes.
- Organ view: when a user expands an organ card, the header shows the organ’s average % and badge counts; the meter should animate to the new `avg_pct` and label the selected context (e.g., "ORGAN-IV — Orchestration"), with gate strips reflecting only that organ’s repos.
- Repo view: the meter becomes the repo’s `%` inside `progress_detail.html`, while the gate strip highlights which gates passed/failed. Add a small label indicating "Recontextualizing: ORGAN-IV → repo-name" so viewers see the nesting.
- Feature/atom view (future): allow selecting a gate or atom from the repo detail; the same meter should display that atom’s completion %, with a short description (sourced from the new `atom` data field).
- Always animate the transition (existing CSS/JS can be extended) so the meter feels like it’s morphing as you zoom in/out.

## Validation & expectations
- Ensure the spec references `/progress/` route and templates, so engineers know where to plug in data.
- Document the gating pipeline: `_eval_gate` returns gate statuses; `promo_ready` flags drive the organ-level summaries. The spec should remind them to keep those calculations in sync when adding deeper contexts.
- Suggested tests: registry updates should update all three contexts (system/organ/repo). Write a dashboard integration test that fetches `/progress/api` and asserts the `context_hierarchy` path updates when selecting an organ or repo.

## Related docs
- `system-dashboard/src/dashboard/routes/progress.py` – gate evaluation and data cache.
- `system-dashboard/templates/progress.html` – macro/organ view layout.
- `system-dashboard/templates/progress_detail.html` – repo detail view.
- `organvm-corpvs-testamentvm/docs/strategy/there+back-again.md:16` – narrative describing the macro↔micro↔macro transition and how Omega/contexts are treated philosophically.
