import { createHash } from "node:crypto";
import { describe, it, expect } from "vitest";
import {
  TESTAMENT_EVENTS,
  getTestamentEventById,
  getTestamentEvents,
} from "@/data/testament-events";
import {
  GENESIS_PREV_HASH,
  KIND_TIER,
  TIER_META,
  canonicalJson,
  classifyKindTier,
  computeAnchorHash,
  computeEventHash,
  computeMerkleRoot,
  sha256Hex,
  verifyCheckpoint,
  verifyEventChain,
} from "@/lib/testament-chain";

/** Independent SHA-256 via node:crypto, for cross-checking the pure-TS port. */
function nodeSha256Hex(input: string): string {
  return createHash("sha256").update(input, "utf8").digest("hex");
}

describe("sha256Hex", () => {
  it.each([
    ["", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
    ["abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"],
    [
      "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
      "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1",
    ],
    ["The quick brown fox jumps over the lazy dog", "d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592"],
  ])("matches node:crypto for %p", (input, expected) => {
    expect(sha256Hex(input)).toBe(expected);
    expect(sha256Hex(input)).toBe(nodeSha256Hex(input));
  });

  it("matches node:crypto on multi-block and unicode input", () => {
    const long = "a".repeat(1000);
    expect(sha256Hex(long)).toBe(nodeSha256Hex(long));
    const unicode = "héllo wörld — ünïcode ✓";
    expect(sha256Hex(unicode)).toBe(nodeSha256Hex(unicode));
  });
});

describe("canonicalJson", () => {
  it("sorts keys and omits whitespace", () => {
    expect(canonicalJson({ b: 1, a: { d: [2, 1], c: "x" } })).toBe(
      '{"a":{"c":"x","d":[2,1]},"b":1}',
    );
  });
});

describe("testament event feed", () => {
  it("is chronological, sequenced 0..n-1, and fully sourced", () => {
    expect(TESTAMENT_EVENTS.length).toBeGreaterThan(0);
    TESTAMENT_EVENTS.forEach((event, index) => {
      expect(event.sequence).toBe(index);
      expect(Number.isNaN(Date.parse(event.timestamp))).toBe(false);
      expect(event.id).toBeTruthy();
      expect(event.label).toBeTruthy();
      expect(event.summary).toBeTruthy();
      expect(event.provenance).toBeTruthy();
      expect(event.source).toBe("seed");
      expect(event.tier).toBe(classifyKindTier(event.kind));
    });
    const times = TESTAMENT_EVENTS.map((e) => Date.parse(e.timestamp));
    expect([...times].sort((a, b) => a - b)).toEqual(times);
  });

  it("has exactly one checkpoint, last, with merkle_root and anchor", () => {
    const checkpoints = TESTAMENT_EVENTS.filter((e) => e.checkpoint);
    expect(checkpoints).toHaveLength(1);
    expect(checkpoints[0]).toBe(
      TESTAMENT_EVENTS[TESTAMENT_EVENTS.length - 1],
    );
    expect(checkpoints[0].merkle_root).toMatch(/^sha256:[0-9a-f]{64}$/);
    expect(checkpoints[0].anchor).not.toBeNull();
    for (const event of TESTAMENT_EVENTS.filter((e) => !e.checkpoint)) {
      expect(event.merkle_root).toBeNull();
      expect(event.anchor).toBeNull();
    }
  });

  it("kinds all classify to the engine's tier map", () => {
    for (const event of TESTAMENT_EVENTS) {
      expect(KIND_TIER[event.kind]).toBe(event.tier);
    }
    expect(classifyKindTier("not.a.kind")).toBeNull();
  });

  it("getTestamentEvents returns sequence order; getTestamentEventById finds by id", () => {
    expect(getTestamentEvents().map((e) => e.sequence)).toEqual(
      TESTAMENT_EVENTS.map((e) => e.sequence),
    );
    expect(getTestamentEventById("gallery-shipped")?.label).toBe(
      "Testament gallery page shipped",
    );
    expect(getTestamentEventById("no-such-event")).toBeUndefined();
  });
});

describe("verifyEventChain", () => {
  it("verifies the checked-in seed feed", () => {
    const result = verifyEventChain(TESTAMENT_EVENTS);
    expect(result.valid).toBe(true);
    expect(result.eventCount).toBe(TESTAMENT_EVENTS.length);
    expect(result.errors).toEqual([]);
  });

  it("rejects a tampered summary", () => {
    const tampered = TESTAMENT_EVENTS.map((e) => ({ ...e }));
    tampered[1] = { ...tampered[1], summary: "forged summary" };
    const result = verifyEventChain(tampered);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("hash mismatch"))).toBe(true);
  });

  it("rejects a broken prev_hash link", () => {
    const tampered = TESTAMENT_EVENTS.map((e) => ({ ...e }));
    tampered[2] = { ...tampered[2], prev_hash: GENESIS_PREV_HASH };
    const result = verifyEventChain(tampered);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("chain link broken"))).toBe(
      true,
    );
  });

  it("rejects reordered feeds and a dropped middle event", () => {
    const reordered = [TESTAMENT_EVENTS[1], TESTAMENT_EVENTS[0]];
    expect(verifyEventChain(reordered).valid).toBe(false);
    // A dropped middle event breaks the link; a bare prefix is a valid
    // shorter chain (the badge reports its event count), so it is not
    // expected to fail here.
    const dropped = [
      TESTAMENT_EVENTS[0],
      TESTAMENT_EVENTS[2],
      TESTAMENT_EVENTS[3],
    ];
    expect(verifyEventChain(dropped).valid).toBe(false);
  });
});

describe("computeEventHash / computeMerkleRoot / computeAnchorHash", () => {
  it("matches node:crypto on the checked-in events", () => {
    for (const event of TESTAMENT_EVENTS) {
      const { anchor_hash, ...rest } = event;
      const expected = `sha256:${nodeSha256Hex(canonicalJson(rest))}`;
      expect(computeEventHash(rest)).toBe(expected);
      expect(computeEventHash(rest)).toBe(anchor_hash);
    }
  });

  it("matches an independent Merkle computation", () => {
    const leaves = TESTAMENT_EVENTS.slice(0, 3).map((e) => e.anchor_hash);
    const pair = (l: string, r: string) =>
      `sha256:${nodeSha256Hex(
        l.replace(/^sha256:/, "") + r.replace(/^sha256:/, ""),
      )}`;
    let current = [...leaves];
    while (current.length > 1) {
      const next: string[] = [];
      for (let i = 0; i < current.length; i += 2) {
        next.push(pair(current[i], current[i + 1] ?? current[i]));
      }
      current = next;
    }
    expect(computeMerkleRoot(leaves)).toBe(current[0]);
  });
});

describe("verifyCheckpoint", () => {
  it("verifies the seed checkpoint's root and anchor digest", () => {
    const checkpoint = TESTAMENT_EVENTS.find((e) => e.checkpoint);
    expect(checkpoint).toBeDefined();
    const result = verifyCheckpoint(TESTAMENT_EVENTS, checkpoint!);
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("rejects a tampered merkle_root and a tampered anchor digest", () => {
    const checkpoint = TESTAMENT_EVENTS.find((e) => e.checkpoint)!;
    const badRoot = { ...checkpoint, merkle_root: GENESIS_PREV_HASH };
    expect(verifyCheckpoint(TESTAMENT_EVENTS, badRoot).valid).toBe(false);
    const badAnchor = {
      ...checkpoint,
      anchor: { ...checkpoint.anchor!, anchor_hash: GENESIS_PREV_HASH },
    };
    expect(verifyCheckpoint(TESTAMENT_EVENTS, badAnchor).valid).toBe(false);
    // The anchor digest itself recomputes from the engine's rule.
    const expected = computeAnchorHash({
      merkle_root: checkpoint.merkle_root!,
      chain_tip_hash: checkpoint.anchor!.chain_tip_hash,
      sequence_start: checkpoint.anchor!.sequence_start,
      sequence_end: checkpoint.anchor!.sequence_end,
      event_count: checkpoint.anchor!.event_count,
      timestamp: checkpoint.anchor!.timestamp,
    });
    expect(expected).toBe(checkpoint.anchor!.anchor_hash);
  });
});

describe("TIER_META", () => {
  it("covers every tier with a distinct, non-empty color", () => {
    const tiers = Object.keys(TIER_META);
    expect(tiers.sort()).toEqual([
      "governance",
      "infrastructure",
      "milestone",
      "operational",
    ]);
    const colors = tiers.map((t) => TIER_META[t as keyof typeof TIER_META].color);
    expect(new Set(colors).size).toBe(tiers.length);
    for (const color of colors) {
      expect(color.length).toBeGreaterThan(0);
    }
  });
});
