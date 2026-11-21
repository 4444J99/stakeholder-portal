import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, it, expect } from "vitest";
import { TESTAMENT_EVENTS } from "@/data/testament-events";
import { EventDetail } from "@/components/testament/EventDetail";
import { EventTimeline } from "@/components/testament/EventTimeline";

describe("EventTimeline", () => {
  it("renders the chain badge, every event, and the checkpoint marker", () => {
    const html = renderToStaticMarkup(createElement(EventTimeline));
    expect(html).toContain("Chain verified");
    expect(html).toContain("Seed feed");
    for (const event of TESTAMENT_EVENTS) {
      expect(html).toContain(event.label);
      expect(html).toContain(event.kind);
    }
    expect(html).toContain("Checkpoint");
    expect(html).toContain("Merkle root");
  });

  it("renders the drill-down detail for a pre-selected event", () => {
    const event = TESTAMENT_EVENTS.find((e) => e.id === "gallery-shipped")!;
    const html = renderToStaticMarkup(
      createElement(EventTimeline, { initialSelectedId: "gallery-shipped" }),
    );
    // Detail panel: provenance, anchor proof, and the close control.
    expect(html).toContain(event.provenance);
    expect(html).toContain("anchor_hash");
    expect(html).toContain("prev_hash");
    expect(html).toContain("Close event detail");
    // Non-checkpoint events carry no Merkle proof in the detail panel.
    expect(html).not.toContain("merkle_root");
  });

  it("renders the checkpoint proof for the checkpoint event", () => {
    const checkpoint = TESTAMENT_EVENTS.find((e) => e.checkpoint)!;
    const html = renderToStaticMarkup(
      createElement(EventTimeline, { initialSelectedId: checkpoint.id }),
    );
    expect(html).toContain("merkle_root");
    expect(html).toContain("anchor digest");
    expect(html).toContain(checkpoint.provenance);
  });
});

describe("EventDetail", () => {
  it("renders the full record for a plain event", () => {
    const event = TESTAMENT_EVENTS[0];
    const html = renderToStaticMarkup(createElement(EventDetail, { event }));
    expect(html).toContain(event.label);
    expect(html).toContain(event.summary);
    expect(html).toContain(event.provenance);
    expect(html).toContain("Governance");
    expect(html).toContain("sequence");
  });
});
