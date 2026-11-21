import type { TestamentEvent } from "@/data/testament-events";
import { TIER_META, shortHash } from "@/lib/testament-chain";

interface EventDetailProps {
  event: TestamentEvent;
  onClose?: () => void;
}

/** Full record for one timeline event, including its anchor proof. */
export function EventDetail({ event, onClose }: EventDetailProps) {
  const tier = TIER_META[event.tier];
  const date = new Date(event.timestamp).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span
              className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 font-medium"
              style={{ color: tier.color, border: `1px solid ${tier.color}` }}
            >
              {tier.label}
            </span>
            <span className="text-[var(--color-text-muted)]">{event.kind}</span>
            <span className="text-[var(--color-text-muted)]">{date}</span>
            {event.checkpoint && (
              <span className="inline-flex items-center gap-1 rounded-full border border-[var(--color-accent)] px-2.5 py-0.5 font-medium text-[var(--color-accent)]">
                ◆ Checkpoint
              </span>
            )}
          </div>
          <h3 className="mt-3 text-lg font-semibold tracking-tight">
            {event.label}
          </h3>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close event detail"
            className="shrink-0 rounded border border-[var(--color-border)] px-2.5 py-1 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
          >
            Close
          </button>
        )}
      </div>

      <p className="mt-3 text-sm leading-relaxed text-[var(--color-text-secondary)]">
        {event.summary}
      </p>

      {/* Anchor proof — the record a reader can check, not a claim. */}
      <dl className="mt-4 space-y-1.5 border-t border-[var(--color-border)] pt-4 font-mono text-xs">
        <div className="flex flex-wrap gap-x-2">
          <dt className="text-[var(--color-text-muted)]">sequence</dt>
          <dd>{event.sequence}</dd>
        </div>
        <div className="flex flex-wrap gap-x-2">
          <dt className="text-[var(--color-text-muted)]">anchor_hash</dt>
          <dd title={event.anchor_hash}>{shortHash(event.anchor_hash)}…</dd>
        </div>
        <div className="flex flex-wrap gap-x-2">
          <dt className="text-[var(--color-text-muted)]">prev_hash</dt>
          <dd title={event.prev_hash}>{shortHash(event.prev_hash)}…</dd>
        </div>
        {event.merkle_root && (
          <div className="flex flex-wrap gap-x-2">
            <dt className="text-[var(--color-text-muted)]">merkle_root</dt>
            <dd title={event.merkle_root}>{shortHash(event.merkle_root)}…</dd>
          </div>
        )}
        {event.anchor && (
          <div className="flex flex-wrap gap-x-2">
            <dt className="text-[var(--color-text-muted)]">anchor digest</dt>
            <dd title={event.anchor.anchor_hash}>
              {shortHash(event.anchor.anchor_hash)}… (seq{" "}
              {event.anchor.sequence_start}–{event.anchor.sequence_end},{" "}
              {event.anchor.event_count} events)
            </dd>
          </div>
        )}
      </dl>

      <p className="mt-4 text-xs leading-relaxed text-[var(--color-text-muted)]">
        Source: {event.source === "seed" ? "seed feed" : "engine chain"} —{" "}
        {event.provenance}
      </p>
    </div>
  );
}
