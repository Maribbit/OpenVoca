import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createRouter, createMemoryHistory } from "vue-router";

import HomeView from "../src/views/HomeView.vue";
import SettingsView from "../src/views/SettingsView.vue";
import { useSettings } from "../src/composables/useSettings";

const tokenizedSentence = {
  sentence: "A lantern glowed by the window beside the meadow.",
  words: ["lantern", "meadow", "window"],
  tokens: [
    { text: "A", isWord: true, isTarget: false, pos: "DET" },
    { text: "lantern", isWord: true, isTarget: true, pos: "NOUN" },
    { text: "glowed", isWord: true, isTarget: false, pos: "VERB" },
    { text: "by", isWord: true, isTarget: false, pos: "ADP" },
    { text: "the", isWord: true, isTarget: false, pos: "DET" },
    { text: "window", isWord: true, isTarget: true, pos: "NOUN" },
    { text: "beside", isWord: true, isTarget: false, pos: "ADP" },
    { text: "the", isWord: true, isTarget: false, pos: "DET" },
    {
      text: "meadow",
      isWord: true,
      isTarget: true,
      pos: "NOUN",
      trailingSpace: false,
    },
    { text: ".", isWord: false, isTarget: false, trailingSpace: false },
  ],
};

describe("HomeView.vue", () => {
  afterEach(() => {
    vi.useRealTimers();
    useSettings()._reset();
    window.localStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  const targetWordsResponse = { words: ["lantern", "meadow", "window"] };

  /** Create a fetch mock that routes by URL. */
  function mockFetch() {
    return vi.fn((url: string) => {
      if (typeof url === "string" && url.startsWith("/api/target-words")) {
        return Promise.resolve({
          ok: true,
          json: async () => targetWordsResponse,
        });
      }
      if (
        typeof url === "string" &&
        url.startsWith("/api/reading-sentence/next/stream")
      ) {
        return Promise.resolve({
          ok: true,
          body: makeSseStream(tokenizedSentence),
        });
      }
      if (
        typeof url === "string" &&
        url.startsWith("/api/reading-sentence/next")
      ) {
        return Promise.resolve({
          ok: true,
          json: async () => tokenizedSentence,
        });
      }
      if (typeof url === "string" && url.startsWith("/api/tts")) {
        return Promise.resolve({
          ok: true,
          blob: async () =>
            new Blob([new Uint8Array([0xff, 0xfb])], { type: "audio/mpeg" }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      });
    });
  }

  /** Build a ReadableStream that emits SSE progress + complete events. */
  function makeSseStream(data: typeof tokenizedSentence): ReadableStream {
    const encoder = new TextEncoder();
    const wordCount = data.sentence.split(/\s+/).length;
    const lines = [
      `event: progress\ndata: ${JSON.stringify({ wordCount })}\n\n`,
      `event: complete\ndata: ${JSON.stringify(data)}\n\n`,
    ];
    return new ReadableStream({
      start(controller) {
        for (const line of lines) {
          controller.enqueue(encoder.encode(line));
        }
        controller.close();
      },
    });
  }

  function makeRouter() {
    return createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", component: HomeView },
        { path: "/stats", component: { template: "<div>Stats</div>" } },
        { path: "/settings", component: SettingsView },
      ],
    });
  }

  /** Click the composer "Generate" button to transition from composer to reading view. */
  async function generateFromComposer(
    wrapper: ReturnType<typeof mount>,
  ): Promise<void> {
    const generateBtn = wrapper
      .findAll("button")
      .find((b) => b.text().includes("Generate"));
    expect(generateBtn).toBeDefined();
    await generateBtn!.trigger("click");
    await flushPromises();
  }

  it("renders the generated reading sentence", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    vi.stubGlobal("fetch", mockFetch());

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    // Composer is shown first — click Generate to load the sentence
    await generateFromComposer(wrapper);

    // Verify marked words have the correct class
    const markedWord = wrapper
      .findAll("button")
      .find((btn) => btn.text() === "lantern")
      ?.find("span");
    expect(markedWord?.classes()).toContain("border-dotted");
    expect(markedWord?.classes()).toContain("border-b");

    // Verify non-marked words do not have the class
    const regularWord = wrapper
      .findAll("button")
      .find((btn) => btn.text() === "glowed")
      ?.find("span");
    expect(regularWord?.classes()).not.toContain("border-dotted");

    const wordButtons = wrapper
      .findAll("button")
      .map((button) => button.text())
      .filter((text) =>
        tokenizedSentence.tokens.some(
          (token) => token.isWord && token.text === text,
        ),
      );

    expect(wrapper.text()).toContain("MENU");
    expect(wrapper.text()).toContain("Reading");
    expect(wordButtons).toEqual([
      "A",
      "lantern",
      "glowed",
      "by",
      "the",
      "window",
      "beside",
      "the",
      "meadow",
    ]);
    expect(wrapper.text()).toContain("meadow.");
    expect(wrapper.text()).toContain("Hold to continue");
  });

  it("advances only after releasing Space when hold is complete", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");
    vi.useFakeTimers();

    const fetchMock = mockFetch();
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    // Generate from composer to enter reading view
    await generateFromComposer(wrapper);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/reading-sentence/next/stream",
      expect.objectContaining({
        method: "POST",
      }),
    );
    const initialCallCount = fetchMock.mock.calls.length;

    window.dispatchEvent(new KeyboardEvent("keydown", { code: "Space" }));
    vi.advanceTimersByTime(650);
    await flushPromises();

    // Hold complete but not released — should NOT have advanced yet
    expect(fetchMock).toHaveBeenCalledTimes(initialCallCount);

    window.dispatchEvent(new KeyboardEvent("keyup", { code: "Space" }));
    await flushPromises();

    // After release, should show composer (not call fetch directly)
    expect(wrapper.text()).toContain("Generate");
    vi.useRealTimers();
  });

  it("switches UI language to Chinese and persists locale", async () => {
    vi.stubGlobal("fetch", mockFetch());

    const router = makeRouter();
    const wrapper = mount(
      { template: "<router-view />" },
      { global: { plugins: [router] } },
    );
    await router.push("/settings");
    await flushPromises();

    const zhToggle = wrapper
      .findAll("button")
      .find((button) => button.text().includes("中文"));

    expect(zhToggle).toBeDefined();
    await zhToggle!.trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("设置");
    expect(wrapper.text()).toContain("界面");
    const cache = JSON.parse(
      window.localStorage.getItem("openvoca.settings.cache") ?? "{}",
    );
    expect(cache?.interface?.locale).toBe("zh");
  });

  it("applies and persists dark reading theme from inline settings", async () => {
    vi.stubGlobal("fetch", mockFetch());

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    // Generate from composer to access reading view with settings trigger
    await generateFromComposer(wrapper);

    const settingsTrigger = wrapper.find(
      '[data-testid="reading-settings-trigger"]',
    );

    expect(settingsTrigger.exists()).toBe(true);
    await settingsTrigger.trigger("click");
    await flushPromises();

    const darkThemeButton = wrapper.find('button[title="Dark"]');

    expect(darkThemeButton.exists()).toBe(true);
    await darkThemeButton.trigger("click");
    await flushPromises();

    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");

    const cache = window.localStorage.getItem("openvoca.settings.cache");
    expect(cache).not.toBeNull();
    const parsed = JSON.parse(cache!) as Record<string, Record<string, string>>;
    expect(parsed.reading?.theme).toBe("dark");
  });

  it("closes inline settings when clicking the blank overlay", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    vi.stubGlobal("fetch", mockFetch());

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    // Generate from composer to access reading view
    await generateFromComposer(wrapper);

    await wrapper
      .find('[data-testid="reading-settings-trigger"]')
      .trigger("click");
    await flushPromises();

    expect(
      wrapper.find('[data-testid="reading-settings-overlay"]').exists(),
    ).toBe(true);

    await wrapper
      .find('[data-testid="reading-settings-overlay"]')
      .trigger("click");
    await flushPromises();

    expect(
      wrapper.find('[data-testid="reading-settings-overlay"]').exists(),
    ).toBe(false);
  });

  it("shows streaming word count progress during generation", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    const encoder = new TextEncoder();
    let enqueueRef: ReadableStreamDefaultController<Uint8Array> | null = null;

    const fetchMock = vi.fn((url: string) => {
      if (typeof url === "string" && url.startsWith("/api/target-words")) {
        return Promise.resolve({
          ok: true,
          json: async () => targetWordsResponse,
        });
      }
      if (
        typeof url === "string" &&
        url.startsWith("/api/reading-sentence/next/stream")
      ) {
        const stream = new ReadableStream<Uint8Array>({
          start(controller) {
            enqueueRef = controller;
          },
        });
        return Promise.resolve({ ok: true, body: stream });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    // Trigger generate from composer
    await generateFromComposer(wrapper);

    // Send a progress event
    enqueueRef!.enqueue(
      encoder.encode(
        `event: progress\ndata: ${JSON.stringify({ wordCount: 5 })}\n\n`,
      ),
    );
    await flushPromises();

    const progress = wrapper.find('[data-testid="loading-progress"]');
    expect(progress.exists()).toBe(true);
    expect(progress.text()).toContain("5");

    // Send complete event
    enqueueRef!.enqueue(
      encoder.encode(
        `event: complete\ndata: ${JSON.stringify(tokenizedSentence)}\n\n`,
      ),
    );
    enqueueRef!.close();
    await flushPromises();

    // Sentence should now be displayed
    expect(wrapper.text()).toContain("lantern");
    expect(wrapper.find('[data-testid="loading-progress"]').exists()).toBe(
      false,
    );
  });

  it("plays TTS audio from backend when read aloud is clicked", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    let playWasCalled = false;
    let audioSrc = "";

    class FakeAudio {
      src = "";
      onplaying: (() => void) | null = null;
      onended: (() => void) | null = null;
      onerror: (() => void) | null = null;
      play = vi.fn(() => {
        audioSrc = this.src;
        playWasCalled = true;
        // Simulate the playing event
        if (this.onplaying) this.onplaying();
        return Promise.resolve();
      });
      pause = vi.fn();
      constructor(url?: string) {
        if (url) this.src = url;
      }
    }
    vi.stubGlobal("Audio", FakeAudio);

    vi.stubGlobal("fetch", mockFetch());

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();
    await generateFromComposer(wrapper);

    // Find and click the read-aloud button
    const readAloudBtn = wrapper
      .findAll("button")
      .find((b) => b.attributes("title") === "Read aloud");
    expect(readAloudBtn).toBeDefined();
    await readAloudBtn!.trigger("click");
    await flushPromises();

    expect(playWasCalled).toBe(true);
    expect(audioSrc).toContain("/api/tts?text=");
  });
});
