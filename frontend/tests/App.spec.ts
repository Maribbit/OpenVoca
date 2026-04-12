import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createRouter, createMemoryHistory } from "vue-router";

import App from "../src/App.vue";
import { useSettings } from "../src/composables/useSettings";

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/", component: { template: "<div>Home</div>" } }],
  });
}

describe("App.vue update banner", () => {
  afterEach(() => {
    vi.useRealTimers();
    useSettings()._reset();
    window.localStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows banner when update is available", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/update-check") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              checked: true,
              hasUpdate: true,
              currentVersion: "0.9.0",
              latestVersion: "0.10.0",
              url: "https://github.com/example/releases/tag/v0.10.0",
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    const router = makeRouter();
    const wrapper = mount(App, { global: { plugins: [router] } });
    await router.isReady();
    await flushPromises();

    // Banner should not appear before the 3-second delay
    expect(wrapper.find("[data-testid='update-banner']").exists()).toBe(false);

    await vi.runAllTimersAsync();
    await flushPromises();

    expect(wrapper.find("[data-testid='update-banner']").exists()).toBe(true);
    expect(wrapper.text()).toContain("0.10.0");
  });

  it("hides banner when dismissed", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/update-check") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              checked: true,
              hasUpdate: true,
              currentVersion: "0.9.0",
              latestVersion: "0.10.0",
              url: "https://github.com/example/releases/tag/v0.10.0",
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    const router = makeRouter();
    const wrapper = mount(App, { global: { plugins: [router] } });
    await router.isReady();
    await flushPromises();
    await vi.runAllTimersAsync();
    await flushPromises();

    const banner = wrapper.find("[data-testid='update-banner']");
    expect(banner.exists()).toBe(true);

    await banner.find("button").trigger("click");
    await flushPromises();

    expect(wrapper.find("[data-testid='update-banner']").exists()).toBe(false);
  });

  it("does not show banner when no update is available", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/update-check") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              checked: true,
              hasUpdate: false,
              currentVersion: "0.9.0",
              latestVersion: "0.9.0",
              url: "",
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    const router = makeRouter();
    const wrapper = mount(App, { global: { plugins: [router] } });
    await router.isReady();
    await flushPromises();
    await vi.runAllTimersAsync();
    await flushPromises();

    expect(wrapper.find("[data-testid='update-banner']").exists()).toBe(false);
  });
});
