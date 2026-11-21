"use client";

import { useMemo, useState } from "react";
import { getTestamentEvents } from "@/data/testament-events";
import {
  TIER_META,
  shortHash,
  verifyCheckpoint,
  verifyEventChain,
} from "@/lib/testament-chain";
import { EventDetail } from "@/components/testament/EventDetail";

interface EventTimelineProps {
  /** Pre-select an event (used by tests to render the drill-down). */
  initialSelectedId?: string | null;
}

/**
 * Event timeline for the /testament route: tier-colored events, Merkle
 * checkpoint markers, a chain-integrity badge computed live from the feed
 * (never hardcoded), and click-to-drill-down into the full record.
 */
export function EventTimeline({ initialSelectedId = null }: EventTimelineProps) {
  const events = useMemo(() => getTestamentEvents(), []);
  const [selectedId, setSelectedId] = useState<string | null>(
    initialSelectedId,
  );
  const selected = events.find((e) => e.id === selectedId) ?? null;

  const verification = useMemo(() => {
    const chain = verifyEventChain(events);
    const checkpointErrors = events
      .filter((e) => e.checkpoint)
      .flatMap((e) => verifyCheckpoint(events, e).errors);
    const errors = [...chain.errors, ...checkpointErrors];
    return {
      valid: errors.length === 0,
      eventCount: chain.eventCount,
      checkpointCount: events.filter((e) => e.checkpoint).length,
      errors,
    };
  }, [events]);

  return (
    <div className="space-y-4">
      {/* Chain-integrity badge — computed from the feed at render time. */}
      <div
        className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-sm"
        role="status"
      >
        <span
          className="inline-flex items-center gap-1.5 font-medium"
          style={{
            color: verification.valid
              ? "var(--color-fresh)"
              : "var(--color-error)",
          }}
        >
          {verification.valid ? "✓ Chain verified" : "✗ Chain broken"}
        </span>
        <span className="text-[var(--color-text-muted)]">
          {verification.eventCount} events · {verification.checkpointCount}{" "}
          checkpoint{verification.checkpointCount === 1 ? "" : "s"}
        </span>
        <span className="text-xs text-[var(--color-text-muted)]">
          Seed feed — engine export pending; hashes recomputed on every render.
        </span>
        {!verification.valid && (
          <span className="w-full text-xs text-[var(--color-error)]">
            {verification.errors[0]}
          </span>
        )}
      </div>

      {/* Timeline */}
      <ol className="relative space-y-3 border-l border-[var(--color-border)] pl-6">
        {events.map((event) => {
          const tier = TIER_META[event.tier];
          const isSelected = event.id === selectedId;
          const date = new Date(event.timestamp).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
          });
          return (
            <li key={event.id} className="relative">
              <span
                aria-hidden="true"
                className="absolute -left-[31px] top-4 h-3 w-3 rounded-full border-2 border-[var(--color-bg)]"
                style={{ backgroundColor: tier.color }}
              />
              <button
                type="button"
                onClick={() => setSelectedId(isSelected ? null : event.id)}
                aria-expanded={isSelected}
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-left transition-colors hover:border-[var(--color-accent)]"
              >
                <span className="flex flex-wrap items-center gap-2 text-xs">
                  <span
                    className="font-medium"
                    style={{ color: tier.color }}
                  >
                    {tier.label}
                  </span>
                  <span className="text-[var(--color-text-muted)]">
                    {event.kind}
                  </span>
                  <span className="text-[var(--color-text-muted)]">
                    {date}
                  </span>
                  {event.checkpoint && (
                    <span className="inline-flex items-center gap-1 font-medium text-[var(--color-accent)]">
                      ◆ Checkpoint · Merkle root{" "}
                      {event.merkle_root
                        ? `${shortHash(event.merkle_root)}…`
                        : "—"}
                    </span>
                  )}
                </span>
                <span className="mt-1.5 block text-sm font-medium leading-tight">
                  {event.label}
                </span>
                <span className="mt-1 block text-xs leading-relaxed text-[var(--color-text-muted)]">
                  {event.summary}
                </span>
              </button>
            </li>
          );
        })}
      </ol>

      {/* Drill-down */}
      {selected && (
        <EventDetail event={selected} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
}
