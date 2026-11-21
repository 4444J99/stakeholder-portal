/**
 * Testament event feed — the event timeline for the /testament route.
 *
 * SEED FEED. These four events are a checked-in seed, not the live engine
 * chain: the engine's chain lives on the operator machine
 * (`~/.organvm/testament/chain.jsonl`, organvm-engine `ledger/emit.py`) and
 * the portal has no engine dependency to ingest it at build time. The
 * follow-up — an engine export that writes a JSON feed the portal ingests
 * the way `organvm testament render --write` already refreshes
 * `testament.ts` — is tracked separately (see organvm-engine #54).
 * Until then, every event here is labelled `source: "seed"` and carries a
 * `provenance` naming the exact repo commit the fact comes from; no event
 * is invented. Do not present seed events as live chain data.
 *
 * HASH RULE (mirrors organvm-engine `ledger/chain.py`, `ledger/merkle.py`,
 * `ledger/anchor.py` — see `src/lib/testament-chain.ts`):
 * - Each event's `anchor_hash` is SHA-256 over canonical JSON (sorted
 *   keys, no whitespace) of every field except `anchor_hash` itself.
 *   (The engine calls this field `hash`; the portal plan calls it
 *   `anchor_hash`. It is the event's own chain hash — not to be confused
 *   with the checkpoint `anchor.anchor_hash`, which digests a whole batch.)
 * - `prev_hash` links to the previous event's `anchor_hash`; the first
 *   event links to `sha256:` + 64 zeroes (the engine's GENESIS_PREV_HASH).
 * - A checkpoint event's `merkle_root` covers the batch it closes — the
 *   `anchor_hash`es of all preceding events — and its `anchor` record is
 *   the engine's AnchorRecord digest over that root.
 * The hashes below were computed with that rule (cross-checked with an
 * independent node:crypto implementation); `verifyEventChain` /
 * `verifyCheckpoint` in `src/lib/testament-chain.ts` recompute them, and
 * the test suite fails if any value drifts.
 */

export type TestamentTier =
  | "governance"
  | "milestone"
  | "operational"
  | "infrastructure";

/** The engine's AnchorRecord digest for one checkpoint batch. */
export interface TestamentAnchor {
  merkle_root: string;
  chain_tip_hash: string;
  sequence_start: number;
  sequence_end: number;
  event_count: number;
  timestamp: string;
  anchor_hash: string;
}

export interface TestamentEvent {
  id: string;
  sequence: number;
  /** ISO-8601 UTC timestamp of the underlying commit. */
  timestamp: string;
  tier: TestamentTier;
  /** Engine event type, e.g. `testament.genesis` (see KIND_TIER). */
  kind: string;
  label: string;
  summary: string;
  /** Hash of the previous event's anchor_hash (`sha256:0…0` for seq 0). */
  prev_hash: string;
  /** This event's own chain hash (SHA-256 over canonical JSON). */
  anchor_hash: string;
  /** Merkle root over the batch this checkpoint closes; null otherwise. */
  merkle_root: string | null;
  checkpoint: boolean;
  /** AnchorRecord digest for the closed batch; null on non-checkpoints. */
  anchor: TestamentAnchor | null;
  /** `"seed"` until the engine export lands; then `"engine-chain"`. */
  source: "seed" | "engine-chain";
  /** Verifiable fact this event cites: repo + commit + what. */
  provenance: string;
}

/**
 * Seed feed, chronological by commit time. All four events are real,
 * dated milestones in the testament's own history.
 */
export const TESTAMENT_EVENTS: TestamentEvent[] = [
  {
    id: "testament-genesis",
    sequence: 0,
    timestamp: "2026-03-20T03:51:01Z",
    tier: "governance",
    kind: "testament.genesis",
    label: "Testament Protocol chain created",
    summary:
      "The native hash-linked event chain lands in organvm-engine (ledger/chain.py): every event hashed over canonical JSON, each linked to its predecessor. The chain this badge verifies starts here.",
    prev_hash:
      "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    anchor_hash:
      "sha256:0576f09a7f3d691e15054640f20724473b7355aa792aca682a1de68f5d236b67",
    merkle_root: null,
    checkpoint: false,
    anchor: null,
    source: "seed",
    provenance:
      "organvm-engine 596d4c7 (2026-03-19): ledger/chain.py — native hash-linked event chain",
  },
  {
    id: "self-portrait-published",
    sequence: 1,
    timestamp: "2026-03-20T04:37:57Z",
    tier: "milestone",
    kind: "content.published",
    label: "Generative self-portrait published",
    summary:
      "The testament module lands in organvm-engine: the system renders its own density into visual art, schematics, statistics, and prose from the same algorithms that govern it.",
    prev_hash:
      "sha256:0576f09a7f3d691e15054640f20724473b7355aa792aca682a1de68f5d236b67",
    anchor_hash:
      "sha256:f6b2bbc7056fdb320b03b3620b077b6d8d9f1735ff76c281e8c31c1cc16feb0c",
    merkle_root: null,
    checkpoint: false,
    anchor: null,
    source: "seed",
    provenance:
      "organvm-engine e63720a (2026-03-20): testament module — generative self-portrait",
  },
  {
    id: "gallery-shipped",
    sequence: 2,
    timestamp: "2026-03-20T12:18:04Z",
    tier: "milestone",
    kind: "content.published",
    label: "Testament gallery page shipped",
    summary:
      "The /testament route goes live in the stakeholder portal (SP #26): the generative self-portrait as a public gallery — system artifacts and organ identity cards.",
    prev_hash:
      "sha256:f6b2bbc7056fdb320b03b3620b077b6d8d9f1735ff76c281e8c31c1cc16feb0c",
    anchor_hash:
      "sha256:892f50c81f3e8e4614413d43d4e5e06f8a34b99f110d139fafe1fc4a55db1d35",
    merkle_root: null,
    checkpoint: false,
    anchor: null,
    source: "seed",
    provenance:
      "stakeholder-portal af5cd8d (2026-03-20): /testament gallery page — SP #26",
  },
  {
    id: "anchor-foundation-checkpoint",
    sequence: 3,
    timestamp: "2026-03-21T19:08:35Z",
    tier: "governance",
    kind: "testament.checkpoint",
    label: "Chain anchor foundation + seed checkpoint",
    summary:
      "The anchor foundation lands in organvm-engine (ledger/anchor.py, commit dbd7da6, referencing #54): Merkle roots can be anchored for external verification. This event checkpoints the seed batch — its Merkle root covers the three events before it.",
    prev_hash:
      "sha256:892f50c81f3e8e4614413d43d4e5e06f8a34b99f110d139fafe1fc4a55db1d35",
    anchor_hash:
      "sha256:646fe33b51b2bf099c376493fb7f2a932d493d2a4fa8879754fe1558803258dc",
    merkle_root:
      "sha256:b9245868acc34b5127a0e6a4b24b591f99c65ec83498ff5476a1600cec4240a9",
    checkpoint: true,
    anchor: {
      merkle_root:
        "sha256:b9245868acc34b5127a0e6a4b24b591f99c65ec83498ff5476a1600cec4240a9",
      chain_tip_hash:
        "sha256:892f50c81f3e8e4614413d43d4e5e06f8a34b99f110d139fafe1fc4a55db1d35",
      sequence_start: 0,
      sequence_end: 2,
      event_count: 3,
      timestamp: "2026-03-21T19:08:35Z",
      anchor_hash:
        "sha256:2f26e12a1a47a957c054e0f6116b736b0473d3963be088ed2f35e675ef8008f6",
    },
    source: "seed",
    provenance:
      "organvm-engine dbd7da6 (2026-03-21): ledger/anchor.py — chain anchor foundation (#54)",
  },
];

export function getTestamentEvents(): TestamentEvent[] {
  return [...TESTAMENT_EVENTS].sort((a, b) => a.sequence - b.sequence);
}

export function getTestamentEventById(
  id: string,
): TestamentEvent | undefined {
  return TESTAMENT_EVENTS.find((e) => e.id === id);
}
