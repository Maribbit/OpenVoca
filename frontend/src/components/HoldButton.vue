<template>
  <div
    class="relative flex flex-col items-center cursor-pointer select-none"
    @mousedown.prevent="startHold"
    @mouseup="releaseHold"
    @mouseleave="abortHold"
    @touchstart.prevent="startHold"
    @touchend="releaseHold"
    @touchcancel="abortHold"
  >
    <div
      class="relative flex items-center overflow-hidden rounded-full border px-8 py-3 transition-transform active:scale-95"
      :class="
        holdReady
          ? 'border-transparent'
          : 'border-black/10 bg-surface shadow-sm'
      "
    >
      <!-- Progress fill -->
      <div
        class="absolute left-0 top-0 h-full rounded-full"
        :class="
          holdReady
            ? 'bg-emerald-500 shadow-[0_0_14px_rgba(16,185,129,0.35)]'
            : 'bg-ink/8'
        "
        :style="{
          width: holdProgress * 100 + '%',
          transitionProperty: 'width',
          transitionDuration: holdProgress > 0 && !holdReady ? '600ms' : '0ms',
          transitionTimingFunction: 'linear',
        }"
      />
      <!-- Label -->
      <p
        class="relative z-10 uppercase tracking-[0.35em] transition-colors duration-150"
        :class="[
          holdReady ? 'text-white' : 'text-inkLight/55',
          headerSizeClass,
        ]"
      >
        {{ holdText }}
      </p>
    </div>

    <!-- Release hint (appears when hold is complete) -->
    <p
      class="absolute -bottom-7 text-xs font-bold uppercase tracking-widest text-emerald-500 transition-all duration-200"
      :class="
        holdReady ? 'translate-y-0 opacity-100' : 'translate-y-1 opacity-0'
      "
    >
      {{ releaseText }}
    </p>
  </div>
</template>

<script setup lang="ts">
  import { ref } from "vue";

  const props = defineProps<{
    disabled: boolean;
    holdText: string;
    releaseText: string;
    headerSizeClass: string;
  }>();

  const emit = defineEmits<{
    advance: [];
  }>();

  const holdProgress = ref(0);
  const holdReady = ref(false);
  let holdTimer: ReturnType<typeof setTimeout> | null = null;

  function startHold(): void {
    if (props.disabled) return;
    abortHold();
    holdProgress.value = 1;
    holdReady.value = false;
    holdTimer = setTimeout(() => {
      holdTimer = null;
      holdReady.value = true;
    }, 600);
  }

  function abortHold(): void {
    if (holdTimer) {
      clearTimeout(holdTimer);
      holdTimer = null;
    }
    holdProgress.value = 0;
    holdReady.value = false;
  }

  function releaseHold(): void {
    const shouldAdvance = holdReady.value;
    abortHold();
    if (shouldAdvance) {
      emit("advance");
    }
  }

  defineExpose({ startHold, releaseHold, abortHold });
</script>
