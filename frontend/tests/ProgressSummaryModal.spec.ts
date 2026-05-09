import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ProgressSummaryModal, {
  type WordProgress,
} from "../src/components/ProgressSummaryModal.vue";

const messages = {
  progressSummaryTitle: "Review Progress",
  progressSummaryDesc: "Check your vocabulary changes.",
  progressRecognized: "Recognized",
  progressUnknown: "Needs review",
  progressNew: "New word",
  progressBack: "Back",
  progressSubmit: "Submit",
  progressEmpty: "No vocabulary updates.",
  editLemma: "Edit lemma",
};

const words: WordProgress[] = [
  { lemma: "evaporate", type: "recognized", currentLevel: 1, newLevel: 2 },
  { lemma: "opaque", type: "unknown", currentLevel: 3, newLevel: 2 },
  { lemma: "luminous", type: "new", newLevel: 1 },
];

describe("ProgressSummaryModal.vue", () => {
  it("uses theme-aware level delta badges", () => {
    const wrapper = mount(ProgressSummaryModal, {
      props: {
        words,
        messages,
      },
    });

    const levelDeltas = wrapper.findAll('[data-testid="level-delta"]');
    expect(levelDeltas).toHaveLength(3);

    for (const delta of levelDeltas) {
      const classes = delta.classes();
      expect(classes).toContain("bg-ink/4");
      expect(classes).toContain("dark:bg-white/8");
      expect(classes).toContain("border-ink/8");
      expect(classes).toContain("dark:border-white/10");
      expect(
        classes.some((className) => className.startsWith("bg-gray-")),
      ).toBe(false);
    }

    const newBadgeClasses = wrapper
      .find('[data-testid="new-word-badge"]')
      .classes();
    expect(newBadgeClasses).toContain("border-ink/15");
    expect(newBadgeClasses).toContain("dark:border-white/15");
  });

  it("emits normalized lemma edits", async () => {
    const wrapper = mount(ProgressSummaryModal, {
      props: {
        words,
        messages,
      },
    });

    await wrapper.find('[data-testid="lemma-edit-trigger"]').trigger("click");
    await wrapper.find('[data-testid="lemma-edit-input"]').setValue(" Vapor ");
    await wrapper.find('[data-testid="lemma-edit-save"]').trigger("click");

    expect(wrapper.emitted("lemma-change")?.[0]).toEqual([
      "evaporate",
      "vapor",
    ]);
  });
});
