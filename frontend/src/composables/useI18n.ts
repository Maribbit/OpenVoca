import { computed, ref } from "vue";

export type Locale = "en" | "zh";

interface LocaleMessages {
  menu: string;
  reading: string;
  loadingSentence: string;
  ollamaError: string;
  refreshHint: string;
  preferences: string;
  closeMenu: string;
  llmConfiguration: string;
  provider: string;
  localModelProvider: string;
  model: string;
  learningParameters: string;
  targetWords: string;
  targetWordsHint: string;
  promptEngineering: string;
  resetToDefault: string;
  generationPrompt: string;
  targetWordsTokenHintPrefix: string;
  targetWordsTokenHintSuffix: string;
  menuErrorMissingWords: string;
  menuErrorMissingPrompt: string;
  cancel: string;
  saveChanges: string;
  language: string;
}

const STORAGE_KEY = "openvoca.ui.locale";

export const MESSAGES: Record<Locale, LocaleMessages> = {
  en: {
    menu: "Menu",
    reading: "Reading",
    loadingSentence: "Asking gemma3:4b for one sentence...",
    ollamaError: "Unable to reach the local Ollama model.",
    refreshHint: "Refresh the page for another sentence",
    preferences: "Preferences",
    closeMenu: "Close menu",
    llmConfiguration: "LLM Configuration",
    provider: "Provider",
    localModelProvider: "Local Model (Ollama)",
    model: "Model",
    learningParameters: "Learning Parameters",
    targetWords: "Target Words",
    targetWordsHint: "Separate words with commas or new lines.",
    promptEngineering: "Prompt Engineering",
    resetToDefault: "Reset to default",
    generationPrompt: "Generation Prompt",
    targetWordsTokenHintPrefix: "Use",
    targetWordsTokenHintSuffix:
      "where the menu should inject the selected words.",
    menuErrorMissingWords: "Add at least one target word.",
    menuErrorMissingPrompt: "Generation prompt cannot be empty.",
    cancel: "Cancel",
    saveChanges: "Save Changes",
    language: "Language",
  },
  zh: {
    menu: "菜单",
    reading: "阅读",
    loadingSentence: "正在向 gemma3:4b 请求一句例句...",
    ollamaError: "无法连接本地 Ollama 模型。",
    refreshHint: "刷新页面即可生成下一句",
    preferences: "偏好设置",
    closeMenu: "关闭菜单",
    llmConfiguration: "模型配置",
    provider: "提供商",
    localModelProvider: "本地模型 (Ollama)",
    model: "模型",
    learningParameters: "学习参数",
    targetWords: "目标词",
    targetWordsHint: "使用逗号或换行分隔多个单词。",
    promptEngineering: "提示词设置",
    resetToDefault: "恢复默认",
    generationPrompt: "生成提示词",
    targetWordsTokenHintPrefix: "在提示词中使用",
    targetWordsTokenHintSuffix: "来注入目标词。",
    menuErrorMissingWords: "请至少输入一个目标词。",
    menuErrorMissingPrompt: "生成提示词不能为空。",
    cancel: "取消",
    saveChanges: "保存修改",
    language: "语言",
  },
};

function detectInitialLocale(): Locale {
  if (typeof window === "undefined") {
    return "en";
  }

  const savedValue = window.localStorage.getItem(STORAGE_KEY);
  if (savedValue === "en" || savedValue === "zh") {
    return savedValue;
  }

  const browserLanguage = window.navigator.language.toLowerCase();
  return browserLanguage.startsWith("zh") ? "zh" : "en";
}

export function useI18n() {
  const locale = ref<Locale>(detectInitialLocale());

  const messages = computed(() => MESSAGES[locale.value]);

  function setLocale(nextLocale: Locale): void {
    locale.value = nextLocale;
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, nextLocale);
    }
  }

  return {
    locale,
    messages,
    setLocale,
  };
}
