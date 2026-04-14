import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import DefinitionToast from "../src/components/DefinitionToast.vue";
import type { DictionaryEntry } from "../src/api/reading";

function makeFakeAudio() {
  let instance: {
    src: string;
    onplaying: (() => void) | null;
    onended: (() => void) | null;
    onerror: (() => void) | null;
    play: ReturnType<typeof vi.fn>;
    pause: ReturnType<typeof vi.fn>;
  } | null = null;

  class FakeAudio {
    src = "";
    onplaying: (() => void) | null = null;
    onended: (() => void) | null = null;
    onerror: (() => void) | null = null;
    play = vi.fn(() => {
      if (this.onplaying) this.onplaying();
      return Promise.resolve();
    });
    pause = vi.fn();
    constructor(url?: string) {
      if (url) this.src = url;
      // eslint-disable-next-line @typescript-eslint/no-this-alias
      instance = this;
    }
  }

  return {
    FakeAudio,
    getInstance: () => instance,
  };
}

const sampleEntry: DictionaryEntry = {
  word: "lantern",
  phonetic: "ˈlæn.tɚn",
  pos: "noun",
  translation: "灯笼",
  definition: "a light inside a container",
};

describe("DefinitionToast.vue", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  function mountToast(entry: DictionaryEntry | null = sampleEntry) {
    return mount(DefinitionToast, {
      props: {
        entry,
        notFoundWord: entry ? null : "xyzzy",
        notFoundText: "No definition found",
        knowText: "Know",
        dontKnowText: "Don't know",
        isMarked: false,
        displayMode: "both",
        pronounceLabel: "Pronounce",
      },
    });
  }

  it("renders the speak-word button", () => {
    const wrapper = mountToast();
    const btn = wrapper.find('[data-testid="speak-word"]');
    expect(btn.exists()).toBe(true);
    expect(btn.attributes("title")).toBe("Pronounce");
  });

  it("plays word audio via /api/tts when speak button is clicked", async () => {
    const { FakeAudio, getInstance } = makeFakeAudio();
    vi.stubGlobal("Audio", FakeAudio);

    const wrapper = mountToast();
    await wrapper.find('[data-testid="speak-word"]').trigger("click");
    await flushPromises();

    const audio = getInstance();
    expect(audio).not.toBeNull();
    expect(audio!.src).toContain("/api/tts?text=lantern");
    expect(audio!.play).toHaveBeenCalled();
  });

  it("falls back to browser SpeechSynthesis on audio error", async () => {
    const { FakeAudio, getInstance } = makeFakeAudio();
    vi.stubGlobal("Audio", FakeAudio);

    const speakMock = vi.fn();
    vi.stubGlobal("speechSynthesis", {
      speak: speakMock,
      cancel: vi.fn(),
    });
    vi.stubGlobal(
      "SpeechSynthesisUtterance",
      class {
        lang = "";
        onend: (() => void) | null = null;
        constructor(public text: string) {}
      },
    );

    const wrapper = mountToast();
    await wrapper.find('[data-testid="speak-word"]').trigger("click");
    await flushPromises();

    // Simulate audio error
    const audio = getInstance();
    audio!.onerror!();
    await flushPromises();

    expect(speakMock).toHaveBeenCalledTimes(1);
  });

  it("stops playback when clicked while speaking", async () => {
    const { FakeAudio, getInstance } = makeFakeAudio();
    vi.stubGlobal("Audio", FakeAudio);

    const wrapper = mountToast();
    const btn = wrapper.find('[data-testid="speak-word"]');

    // Start playback
    await btn.trigger("click");
    await flushPromises();

    const audio = getInstance();
    expect(audio!.play).toHaveBeenCalled();

    // Click again while speaking — should stop
    await btn.trigger("click");
    await flushPromises();

    expect(audio!.pause).toHaveBeenCalled();
  });

  it("uses notFoundWord when entry is null", async () => {
    const { FakeAudio, getInstance } = makeFakeAudio();
    vi.stubGlobal("Audio", FakeAudio);

    const wrapper = mount(DefinitionToast, {
      props: {
        entry: null,
        notFoundWord: "xyzzy",
        notFoundText: "No definition found",
        knowText: "Know",
        dontKnowText: "Don't know",
        isMarked: false,
        displayMode: "both",
        pronounceLabel: "Pronounce",
      },
    });

    await wrapper.find('[data-testid="speak-word"]').trigger("click");
    await flushPromises();

    const audio = getInstance();
    expect(audio).not.toBeNull();
    expect(audio!.src).toContain("/api/tts?text=xyzzy");
  });
});
