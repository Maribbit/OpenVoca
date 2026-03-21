import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import HomeView from "../src/views/HomeView.vue";

describe("HomeView.vue", () => {
  it("renders the welcome text correctly", () => {
    // 挂载组件
    const wrapper = mount(HomeView);

    // 断言内容存在
    expect(wrapper.text()).toContain("Welcome to OpenVoca");
    expect(wrapper.text()).toContain("This is the Home view.");
  });
});
