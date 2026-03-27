<template>
  <section
    data-testid="reading-settings-overlay"
    class="fixed inset-0 z-20 px-4 pt-20"
    @click.self="$emit('close')"
  >
    <div
      class="menu-fade mx-auto flex w-fit max-w-full flex-col items-stretch gap-2 rounded-[26px] border border-black/8 bg-surface/82 p-2 shadow-[0_20px_50px_rgba(44,44,44,0.12)] backdrop-blur-md md:flex-row md:flex-wrap md:items-center md:justify-center md:gap-3"
    >
      <!-- Font size -->
      <div class="flex items-center gap-1 rounded-xl bg-paper p-1">
        <span
          class="px-2 text-xs font-medium uppercase tracking-wide text-inkLight"
        >
          {{ messages.fontSize }}
        </span>
        <button
          v-for="opt in fontSizeOptions"
          :key="opt.value"
          type="button"
          class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
          :class="optionButtonClass(settings.fontSize === opt.value)"
          @click="
            $emit('update:settings', { ...settings, fontSize: opt.value })
          "
        >
          <span :class="opt.labelClass">{{ opt.label }}</span>
        </button>
      </div>

      <!-- Spacing -->
      <div class="flex items-center gap-1 rounded-xl bg-paper p-1">
        <span
          class="px-2 text-xs font-medium uppercase tracking-wide text-inkLight"
        >
          {{ messages.spacing }}
        </span>
        <button
          v-for="opt in spacingOptions"
          :key="opt.value"
          type="button"
          class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
          :class="optionButtonClass(settings.spacing === opt.value)"
          @click="$emit('update:settings', { ...settings, spacing: opt.value })"
        >
          <svg
            class="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              :d="opt.iconPath"
            />
          </svg>
        </button>
      </div>

      <!-- Theme -->
      <div class="flex items-center gap-1 rounded-xl bg-paper p-1">
        <span
          class="px-2 text-xs font-medium uppercase tracking-wide text-inkLight"
        >
          {{ messages.theme }}
        </span>
        <button
          type="button"
          class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
          :class="optionButtonClass(settings.theme === 'light')"
          @click="$emit('update:settings', { ...settings, theme: 'light' })"
          :title="messages.themeLight"
        >
          <svg
            class="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0z"
            />
          </svg>
        </button>
        <button
          type="button"
          class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
          :class="optionButtonClass(settings.theme === 'dark')"
          @click="$emit('update:settings', { ...settings, theme: 'dark' })"
          :title="messages.themeDark"
        >
          <svg
            class="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M20.354 15.354A9 9 0 0 1 8.646 3.646 9.003 9.003 0 0 0 12 21a9.003 9.003 0 0 0 8.354-5.646z"
            />
          </svg>
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
  export type FontSizeOption = "sm" | "md" | "lg";
  export type SpacingOption = "tight" | "normal" | "loose";
  export type ThemeOption = "light" | "dark";

  export interface ReadingUiSettings {
    fontSize: FontSizeOption;
    spacing: SpacingOption;
    theme: ThemeOption;
  }

  defineProps<{
    settings: ReadingUiSettings;
    messages: {
      fontSize: string;
      spacing: string;
      theme: string;
      themeLight: string;
      themeDark: string;
    };
  }>();

  defineEmits<{
    close: [];
    "update:settings": [settings: ReadingUiSettings];
  }>();

  const fontSizeOptions = [
    { value: "sm" as const, label: "A-", labelClass: "text-xs font-medium" },
    { value: "md" as const, label: "A", labelClass: "text-sm font-medium" },
    { value: "lg" as const, label: "A+", labelClass: "text-base font-medium" },
  ];

  const spacingOptions = [
    { value: "tight" as const, iconPath: "M4 8h16M4 16h16" },
    { value: "normal" as const, iconPath: "M4 6h16M4 12h16M4 18h16" },
    { value: "loose" as const, iconPath: "M4 4h16M4 12h16M4 20h16" },
  ];

  function optionButtonClass(isActive: boolean): string {
    return isActive
      ? "bg-surface text-ink shadow-sm"
      : "text-inkLight hover:bg-surface hover:text-ink";
  }
</script>
