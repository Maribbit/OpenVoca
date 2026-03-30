import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createRouter, createMemoryHistory } from "vue-router";

import HomeView from "../src/views/HomeView.vue";
import SettingsView from "../src/views/SettingsView.vue";

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
    window.localStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

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

  it("renders the generated reading sentence", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => tokenizedSentence,
      }),
    );

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    // Verify marked words have the correct class
    const markedWord = wrapper
      .findAll("span")
      .find((span) => span.text() === "lantern");
    expect(markedWord?.classes()).toContain("border-dotted");
    expect(markedWord?.classes()).toContain("border-b");

    // Verify non-marked words do not have the class
    const regularWord = wrapper
      .findAll("span")
      .find((span) => span.text() === "glowed");
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

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => tokenizedSentence,
    });
    vi.stubGlobal("fetch", fetchMock);

    mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/reading-sentence/next",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"targetWordCount":3'),
      }),
    );
    const initialCallCount = fetchMock.mock.calls.length;

    window.dispatchEvent(new KeyboardEvent("keydown", { code: "Space" }));
    vi.advanceTimersByTime(650);
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledTimes(initialCallCount);

    window.dispatchEvent(new KeyboardEvent("keyup", { code: "Space" }));
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/reading-sentence/next",
      expect.any(Object),
    );
    expect(fetchMock.mock.calls.length).toBeGreaterThan(initialCallCount);
    vi.useRealTimers();
  });

  it("switches UI language to Chinese and persists locale", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => tokenizedSentence,
      }),
    );

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
    expect(window.localStorage.getItem("openvoca.ui.locale")).toBe("zh");
  });

  it("applies and persists dark reading theme from inline settings", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => tokenizedSentence,
      }),
    );

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

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

    expect(document.documentElement.getAttribute("data-reading-theme")).toBe(
      "dark",
    );

    expect(
      window.localStorage.getItem("openvoca.reading.ui.settings"),
    ).toContain('"theme":"dark"');
  });

  it("closes inline settings when clicking the blank overlay", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => tokenizedSentence,
      }),
    );

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

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
});
