import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import HomeView from "../src/views/HomeView.vue";

const tokenizedSentence = {
  sentence: "A lantern glowed by the window beside the meadow.",
  words: ["lantern", "meadow", "window"],
  tokens: [
    { text: "A", isWord: true },
    { text: "lantern", isWord: true },
    { text: "glowed", isWord: true },
    { text: "by", isWord: true },
    { text: "the", isWord: true },
    { text: "window", isWord: true },
    { text: "beside", isWord: true },
    { text: "the", isWord: true },
    { text: "meadow", isWord: true },
    { text: ".", isWord: false },
  ],
};

describe("HomeView.vue", () => {
  afterEach(() => {
    window.localStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders the generated reading sentence", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => tokenizedSentence,
      }),
    );

    const wrapper = mount(HomeView);
    await flushPromises();
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
    expect(wrapper.text()).toContain("Refresh the page for another sentence");
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

    const wrapper = mount(HomeView);
    await flushPromises();

    const menuTrigger = wrapper
      .findAll("button")
      .find((button) => button.text().includes("MENU"));

    expect(menuTrigger).toBeDefined();
    await menuTrigger!.trigger("click");

    const zhToggle = wrapper
      .findAll("button")
      .find((button) => button.text().includes("中文"));

    expect(zhToggle).toBeDefined();
    await zhToggle!.trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("菜单");
    expect(wrapper.text()).toContain("偏好设置");
    expect(wrapper.text()).toContain("保存修改");
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

    const wrapper = mount(HomeView);
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

    const wrapper = mount(HomeView);
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
