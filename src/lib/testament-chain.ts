/**
 * Testament chain verification — pure TypeScript, no Node-only imports,
 * so the same code runs in the browser bundle, in Node, and in tests.
 *
 * Mirrors the engine's rules in 4444J99/organvm-engine:
 * - `ledger/chain.py`: GENESIS_PREV_HASH, compute_event_hash (SHA-256 over
 *   canonical JSON — sorted keys, no whitespace — of every field except the
 *   hash itself), chain invariant event[n].prev_hash == event[n-1].hash.
 * - `ledger/merkle.py`: pairwise SHA-256 over concatenated hex (no prefix),
 *   odd last leaf duplicated, root is the single top element.
 * - `ledger/anchor.py`: compute_anchor_hash over canonical JSON of
 *   {chain_tip_hash, event_count, merkle_root, sequence_end, sequence_start,
 *   timestamp}.
 * - `ledger/tiers.py`: the EventTier taxonomy and the kind -> tier map.
 *
 * One deliberate difference: the engine calls an event's own hash `hash`;
 * the portal plan (organvm-engine #54) calls it `anchor_hash`, so the
 * portal field is `anchor_hash`. The checkpoint `anchor` record below is
 * the engine's AnchorRecord digest — a different hash that attests to a
 * whole batch, not to a single event.
 */
import type { TestamentEvent, TestamentTier } from "@/data/testament-events";

/** First event's prev_hash, identical to the engine's GENESIS_PREV_HASH. */
export const GENESIS_PREV_HASH = `sha256:${"0".repeat(64)}`;

/**
 * Tier presentation — colors reuse the portal's existing tokens only
 * (--color-accent / --color-fresh / --color-warn / --color-text-muted),
 * so the timeline needs no new palette.
 */
export const TIER_META: Record<
  TestamentTier,
  { label: string; color: string; description: string }
> = {
  governance: {
    label: "Governance",
    color: "var(--color-accent)",
    description: "Decisions and attestations that bind the system.",
  },
  milestone: {
    label: "Milestone",
    color: "var(--color-fresh)",
    description: "Published work and public announcements.",
  },
  operational: {
    label: "Operational",
    color: "var(--color-warn)",
    description: "Routine updates, bundled into digests.",
  },
  infrastructure: {
    label: "Infrastructure",
    color: "var(--color-text-muted)",
    description: "Chain-only plumbing, not syndicated.",
  },
};

/**
 * Kind -> tier map, copied from the engine's `ledger/tiers.py` TIER_MAP so
 * the portal classifies event kinds exactly the way the engine does.
 */
export const KIND_TIER: Record<string, TestamentTier> = {
  "governance.promotion": "governance",
  "governance.audit": "governance",
  "governance.dependency_change": "governance",
  "testament.genesis": "governance",
  "testament.checkpoint": "governance",
  "testament.verified": "governance",
  "ci.health": "milestone",
  "content.published": "milestone",
  "ecosystem.mutation": "milestone",
  "pitch.generated": "milestone",
  "registry.update": "operational",
  "seed.update": "operational",
  "metrics.update": "operational",
  "context.sync": "operational",
  "entity.created": "operational",
  "entity.archived": "operational",
  "ontologia.variable": "operational",
  "git.sync": "infrastructure",
  "agent.punch_in": "infrastructure",
  "agent.punch_out": "infrastructure",
  "agent.tool_lock": "infrastructure",
};

export function classifyKindTier(kind: string): TestamentTier | null {
  return KIND_TIER[kind] ?? null;
}

// ---------------------------------------------------------------------------
// SHA-256 (FIPS 180-4), dependency-free so the browser bundle can verify.
// ---------------------------------------------------------------------------

const SHA256_K = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
  0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
  0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
  0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
  0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
  0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
  0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
  0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
  0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

function rotr(x: number, n: number): number {
  return (x >>> n) | (x << (32 - n));
}

/** SHA-256 hex digest of a UTF-8 string. */
export function sha256Hex(input: string): string {
  const bytes = new TextEncoder().encode(input);
  const bitLen = bytes.length * 8;
  const paddedLen = (((bytes.length + 9 + 63) >> 6) << 6);
  const padded = new Uint8Array(paddedLen);
  padded.set(bytes);
  padded[bytes.length] = 0x80;
  const view = new DataView(padded.buffer);
  view.setUint32(paddedLen - 8, Math.floor(bitLen / 0x100000000), false);
  view.setUint32(paddedLen - 4, bitLen >>> 0, false);

  let h0 = 0x6a09e667;
  let h1 = 0xbb67ae85;
  let h2 = 0x3c6ef372;
  let h3 = 0xa54ff53a;
  let h4 = 0x510e527f;
  let h5 = 0x9b05688c;
  let h6 = 0x1f83d9ab;
  let h7 = 0x5be0cd19;

  const w = new Array<number>(64);
  for (let off = 0; off < paddedLen; off += 64) {
    for (let i = 0; i < 16; i++) {
      w[i] = view.getUint32(off + i * 4, false);
    }
    for (let i = 16; i < 64; i++) {
      const s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
      const s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
      w[i] = (w[i - 16] + s0 + w[i - 7] + s1) | 0;
    }
    let a = h0;
    let b = h1;
    let c = h2;
    let d = h3;
    let e = h4;
    let f = h5;
    let g = h6;
    let h = h7;
    for (let i = 0; i < 64; i++) {
      const s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
      const ch = (e & f) ^ (~e & g);
      const temp1 = (h + s1 + ch + SHA256_K[i] + w[i]) | 0;
      const s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
      const maj = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (s0 + maj) | 0;
      h = g;
      g = f;
      f = e;
      e = (d + temp1) | 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) | 0;
    }
    h0 = (h0 + a) | 0;
    h1 = (h1 + b) | 0;
    h2 = (h2 + c) | 0;
    h3 = (h3 + d) | 0;
    h4 = (h4 + e) | 0;
    h5 = (h5 + f) | 0;
    h6 = (h6 + g) | 0;
    h7 = (h7 + h) | 0;
  }

  return [h0, h1, h2, h3, h4, h5, h6, h7]
    .map((x) => (x >>> 0).toString(16).padStart(8, "0"))
    .join("");
}

/**
 * Canonical JSON: sorted keys, no whitespace — the same form the engine's
 * `json.dumps(sort_keys=True, separators=(",", ":"))` produces. Only the
 * JSON value shapes the feed uses (string / number / boolean / null /
 * array / plain object) are supported.
 */
export function canonicalJson(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "number" || typeof value === "boolean") {
    return JSON.stringify(value);
  }
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) {
    return `[${value.map((v) => canonicalJson(v)).join(",")}]`;
  }
  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    const keys = Object.keys(obj).sort();
    return `{${keys
      .map((k) => `${JSON.stringify(k)}:${canonicalJson(obj[k])}`)
      .join(",")}}`;
  }
  throw new Error(`canonicalJson: unsupported value type ${typeof value}`);
}

// ---------------------------------------------------------------------------
// Event hash, Merkle root, anchor digest — engine rules, ported verbatim.
// ---------------------------------------------------------------------------

/**
 * An event's own chain hash (`anchor_hash`), computed over every field
 * except `anchor_hash` itself — the engine's `ledger.chain.compute_event_hash`.
 */
export function computeEventHash(
  event: Omit<TestamentEvent, "anchor_hash">,
): string {
  return `sha256:${sha256Hex(canonicalJson(event))}`;
}

function hashPair(left: string, right: string): string {
  const l = left.replace(/^sha256:/, "");
  const r = right.replace(/^sha256:/, "");
  return `sha256:${sha256Hex(l + r)}`;
}

/**
 * Merkle root over a list of leaf hashes — the engine's
 * `ledger.merkle.compute_merkle_root` (odd last leaf duplicated).
 */
export function computeMerkleRoot(leaves: string[]): string {
  if (leaves.length === 0) {
    throw new Error("Cannot build Merkle tree from empty leaf list");
  }
  let current = [...leaves];
  while (current.length > 1) {
    const next: string[] = [];
    for (let i = 0; i < current.length; i += 2) {
      const left = current[i];
      const right = i + 1 < current.length ? current[i + 1] : current[i];
      next.push(hashPair(left, right));
    }
    current = next;
  }
  return current[0];
}

export interface AnchorInput {
  merkle_root: string;
  chain_tip_hash: string;
  sequence_start: number;
  sequence_end: number;
  event_count: number;
  timestamp: string;
}

/**
 * A checkpoint batch's anchor digest — the engine's
 * `ledger.anchor.compute_anchor_hash`.
 */
export function computeAnchorHash(input: AnchorInput): string {
  return `sha256:${sha256Hex(canonicalJson(input))}`;
}

// ---------------------------------------------------------------------------
// Verification — what the chain-integrity badge runs.
// ---------------------------------------------------------------------------

export interface ChainVerification {
  valid: boolean;
  eventCount: number;
  errors: string[];
}

/**
 * Full chain verification, mirroring `ledger.chain.verify_chain`: every
 * event's hash recomputes, every prev_hash links to its predecessor, and
 * sequences run 0, 1, 2, ... in feed order.
 */
export function verifyEventChain(events: TestamentEvent[]): ChainVerification {
  const errors: string[] = [];
  let prevHash = GENESIS_PREV_HASH;
  let prevSeq = -1;
  for (const event of events) {
    const { anchor_hash, ...rest } = event;
    if (computeEventHash(rest) !== anchor_hash) {
      errors.push(`Sequence ${event.sequence}: hash mismatch (event tampered)`);
    }
    if (event.prev_hash !== prevHash) {
      errors.push(
        `Sequence ${event.sequence}: chain link broken (prev_hash != predecessor's hash)`,
      );
    }
    if (event.sequence !== prevSeq + 1) {
      errors.push(`Sequence ${event.sequence}: expected ${prevSeq + 1}`);
    }
    prevHash = anchor_hash;
    prevSeq = event.sequence;
  }
  return { valid: errors.length === 0, eventCount: events.length, errors };
}

export interface CheckpointVerification {
  valid: boolean;
  errors: string[];
}

/**
 * Verify one checkpoint event: its merkle_root recomputes from the
 * anchor_hashes of the batch it closes (all preceding events), and its
 * anchor digest recomputes from that root via the engine's anchor rule.
 */
export function verifyCheckpoint(
  events: TestamentEvent[],
  checkpoint: TestamentEvent,
): CheckpointVerification {
  const errors: string[] = [];
  if (!checkpoint.checkpoint) {
    errors.push(`Event ${checkpoint.id} is not a checkpoint`);
    return { valid: false, errors };
  }
  const batch = events.filter((e) => e.sequence < checkpoint.sequence);
  if (batch.length === 0) {
    errors.push(`Checkpoint ${checkpoint.id} covers an empty batch`);
    return { valid: false, errors };
  }
  const root = computeMerkleRoot(batch.map((e) => e.anchor_hash));
  if (checkpoint.merkle_root !== root) {
    errors.push(`Checkpoint ${checkpoint.id}: merkle_root mismatch`);
  }
  if (!checkpoint.anchor) {
    errors.push(`Checkpoint ${checkpoint.id}: missing anchor record`);
    return { valid: false, errors };
  }
  const a = checkpoint.anchor;
  const tip = batch[batch.length - 1];
  if (a.merkle_root !== root) {
    errors.push(`Checkpoint ${checkpoint.id}: anchor merkle_root mismatch`);
  }
  if (a.chain_tip_hash !== tip.anchor_hash) {
    errors.push(`Checkpoint ${checkpoint.id}: anchor chain_tip_hash mismatch`);
  }
  if (
    a.sequence_start !== batch[0].sequence ||
    a.sequence_end !== tip.sequence ||
    a.event_count !== batch.length
  ) {
    errors.push(`Checkpoint ${checkpoint.id}: anchor sequence range mismatch`);
  }
  if (a.timestamp !== checkpoint.timestamp) {
    errors.push(`Checkpoint ${checkpoint.id}: anchor timestamp mismatch`);
  }
  const expected = computeAnchorHash({
    merkle_root: root,
    chain_tip_hash: tip.anchor_hash,
    sequence_start: batch[0].sequence,
    sequence_end: tip.sequence,
    event_count: batch.length,
    timestamp: checkpoint.timestamp,
  });
  if (a.anchor_hash !== expected) {
    errors.push(`Checkpoint ${checkpoint.id}: anchor digest mismatch`);
  }
  return { valid: errors.length === 0, errors };
}

/** First 8 hex chars of a `sha256:` hash, for display. */
export function shortHash(hash: string): string {
  return hash.replace(/^sha256:/, "").slice(0, 8);
}
