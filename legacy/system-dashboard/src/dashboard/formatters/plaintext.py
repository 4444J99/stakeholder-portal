"""Plain-text formatters for terminal-friendly API output.

Designed for 60-column width (Termius iPhone portrait).
Uses Unicode box-drawing — no ANSI colors — so output is safe to
pipe, redirect, or paste into messages.
"""

from __future__ import annotations

import json
from typing import Any


# ── Public API ─────────────────────────────────────────────────────────


def format_response(endpoint: str, data: dict[str, Any]) -> str:
    """Dispatch to a per-endpoint formatter, falling back to indented JSON."""
    formatter = _FORMATTERS.get(endpoint)
    if formatter is None:
        return json.dumps(data, indent=2)
    return formatter(data)


# ── Shared helpers ─────────────────────────────────────────────────────

WIDTH = 60


def _box(title: str, lines: list[str]) -> str:
    """Wrap lines in a Unicode box with a title bar."""
    inner = WIDTH - 2
    parts = [
        f"┌{'─' * inner}┐",
        f"│ {title:<{inner - 1}}│",
        f"├{'─' * inner}┤",
    ]
    for line in lines:
        # Truncate if too wide
        display = line[: inner - 1]
        parts.append(f"│ {display:<{inner - 1}}│")
    parts.append(f"└{'─' * inner}┘")
    return "\n".join(parts)


def _table(headers: list[str], rows: list[list[str]]) -> str:
    """Simple column-aligned table. Columns auto-sized within WIDTH."""
    n = len(headers)
    if n == 0:
        return ""
    # Compute column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row[:n]):
            widths[i] = max(widths[i], len(str(cell)))
    # Cap total to WIDTH
    total = sum(widths) + (n - 1) * 3  # separators: " │ "
    if total > WIDTH:
        scale = WIDTH / total
        widths = [max(3, int(w * scale)) for w in widths]

    def _fmt_row(cells: list[str]) -> str:
        parts = []
        for i, cell in enumerate(cells[:n]):
            parts.append(f"{str(cell):<{widths[i]}}")
        return " │ ".join(parts)

    sep = "─┼─".join("─" * w for w in widths)
    out = [_fmt_row(headers), sep]
    for row in rows:
        out.append(_fmt_row(row))
    return "\n".join(out)


def _bar(value: int | float, total: int | float, width: int = 20) -> str:
    """ASCII progress bar: [████░░░░░░] 45%"""
    if total == 0:
        pct = 0.0
    else:
        pct = value / total
    filled = int(pct * width)
    empty = width - filled
    pct_str = f"{pct * 100:.0f}%"
    return f"[{'█' * filled}{'░' * empty}] {pct_str}"


# ── Per-endpoint formatters ────────────────────────────────────────────


def _fmt_status(data: dict[str, Any]) -> str:
    total = data.get("total_repos", 0)
    active = data.get("active_repos", 0)
    archived = data.get("archived_repos", 0)
    ci = data.get("ci_coverage", 0)
    seed = data.get("seed_coverage", 0)
    revenue = data.get("revenue_status", "unknown")
    ts = data.get("timestamp", "")

    lines = [
        f"Repos: {active} active / {archived} archived / {total} total",
        f"CI coverage:   {_bar(ci, 100)}",
        f"Seed coverage: {_bar(seed, 100)}",
        f"Revenue: {revenue}",
    ]

    by_organ = data.get("by_organ", {})
    if by_organ:
        lines.append("")
        lines.append("Per organ:")
        for organ, info in sorted(by_organ.items()):
            if isinstance(info, dict):
                count = info.get("total", info.get("repos", "?"))
                lines.append(f"  {organ}: {count} repos")
            else:
                lines.append(f"  {organ}: {info}")

    if ts:
        lines.append("")
        lines.append(f"As of {ts}")

    return _box("ORGANVM STATUS", lines)


def _fmt_omega(data: dict[str, Any]) -> str:
    met = data.get("met_count", 0)
    total = data.get("total_criteria", 0)
    criteria = data.get("criteria", [])

    lines = [
        f"Progress: {met}/{total} {_bar(met, total)}",
        "",
    ]
    for c in criteria:
        name = c.get("name", "?")
        is_met = c.get("met", False)
        mark = "✓" if is_met else "✗"
        lines.append(f"  {mark} {name}")

    return _box("OMEGA SCORECARD", lines)


def _fmt_registry(data: dict[str, Any]) -> str:
    repos = data.get("repos", [])
    total = data.get("total", len(repos))

    headers = ["Name", "Organ", "Tier", "Status"]
    rows = []
    for r in repos:
        rows.append([
            str(r.get("name", "")),
            str(r.get("organ", "")),
            str(r.get("tier", "")),
            str(r.get("promotion_status", "")),
        ])

    parts = [f"Total: {total} repos", ""]
    parts.append(_table(headers, rows))
    return _box("REGISTRY", parts)


def _fmt_governance_audit(data: dict[str, Any]) -> str:
    passed = data.get("passed", False)
    critical = data.get("critical", [])
    warnings = data.get("warnings", [])

    verdict = "PASSED ✓" if passed else "FAILED ✗"
    lines = [f"Verdict: {verdict}", ""]

    if critical:
        lines.append(f"Critical ({len(critical)}):")
        for item in critical:
            lines.append(f"  ✗ {item}")
        lines.append("")

    if warnings:
        lines.append(f"Warnings ({len(warnings)}):")
        for item in warnings:
            lines.append(f"  ⚠ {item}")

    if not critical and not warnings:
        lines.append("No issues found.")

    return _box("GOVERNANCE AUDIT", lines)


def _fmt_ci(data: dict[str, Any]) -> str:
    ci_status = data.get("status", "unknown")
    with_ci = data.get("repos_with_ci", 0)
    without_ci = data.get("repos_without", 0)
    failures = data.get("failures", [])

    lines = [
        f"Status: {ci_status}",
        f"With CI: {with_ci}  │  Without: {without_ci}",
    ]

    if failures:
        lines.append("")
        lines.append(f"Failures ({len(failures)}):")
        for f in failures:
            if isinstance(f, dict):
                lines.append(f"  ✗ {f.get('repo', f.get('name', '?'))}")
            else:
                lines.append(f"  ✗ {f}")

    return _box("CI HEALTH", lines)


def _fmt_coordination_board(data: dict[str, Any]) -> str:
    claims = data.get("claims", [])

    if not claims:
        return _box("COORDINATION BOARD", ["No active claims."])

    headers = ["Agent", "Session", "Scope"]
    rows = []
    for c in claims:
        rows.append([
            str(c.get("agent", "")),
            str(c.get("session", ""))[:12],
            str(c.get("scope", "")),
        ])

    return _box("COORDINATION BOARD", [_table(headers, rows)])


def _fmt_deadlines(data: dict[str, Any]) -> str:
    deadlines = data.get("deadlines", [])
    total_all = data.get("total_all", len(deadlines))
    total_shown = data.get("total_shown", len(deadlines))

    if not deadlines:
        return _box("DEADLINES", ["No upcoming deadlines."])

    lines = [f"Showing {total_shown} of {total_all}", ""]

    for d in deadlines:
        desc = d.get("description", "?")
        date = d.get("date", "?")
        days = d.get("days_remaining", "?")
        urgency = d.get("urgency", "")
        marker = "🔴" if urgency == "critical" else "🟡" if urgency == "warning" else "  "
        lines.append(f"{marker} {date} ({days}d) {desc}")

    return _box("DEADLINES", lines)


# ── Formatter registry ─────────────────────────────────────────────────

_FORMATTERS: dict[str, Any] = {
    "status": _fmt_status,
    "omega": _fmt_omega,
    "registry": _fmt_registry,
    "governance_audit": _fmt_governance_audit,
    "ci": _fmt_ci,
    "coordination_board": _fmt_coordination_board,
    "deadlines": _fmt_deadlines,
}
