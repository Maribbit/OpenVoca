import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import HomeView from "../src/views/HomeView.vue";

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
        json: async () => ({
          sentence: "A lantern glowed by the window beside the meadow.",
          words: ["lantern", "meadow", "window"],
        }),
      }),
    );

    const wrapper = mount(HomeView);
    await flushPromises();

    expect(wrapper.text()).toContain("Menu");
    expect(wrapper.text()).toContain("Reading");
    expect(wrapper.text()).toContain(
      "A lantern glowed by the window beside the meadow.",
    );
    expect(wrapper.text()).toContain("Refresh the page for another sentence");
  });

  it("switches UI language to Chinese and persists locale", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          sentence: "A lantern glowed by the window beside the meadow.",
          words: ["lantern", "meadow", "window"],
        }),
      }),
    );

    const wrapper = mount(HomeView);
    await flushPromises();

    const menuTrigger = wrapper
      .findAll("button")
      .find((button) => button.text().includes("Menu"));

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
});
