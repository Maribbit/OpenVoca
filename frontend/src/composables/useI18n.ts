import { computed, ref } from "vue";

import { useSettings } from "./useSettings";

export type Locale = "en" | "zh";

interface LocaleMessages {
  menu: string;
  readingDisplaySettings: string;
  loadingSentence: string;
  ollamaError: string;
  feedbackError: string;
  provider: string;
  model: string;
  targetWordCount: string;
  targetWordCountHint: string;
  resetToDefault: string;
  targetWordsTokenHintPrefix: string;
  targetWordsTokenHintSuffix: string;
  language: string;
  fontSize: string;
  spacing: string;
  theme: string;
  themeLight: string;
  themeDark: string;
  uiSize: string;
  nextSentenceHint: string;
  releaseHint: string;
  vocabulary: string;
  backToReading: string;
  clearVocabulary: string;
  familiarityNeedsReview: string;
  familiarityLearning: string;
  familiarityFamiliar: string;
  familiarityMastered: string;
  showingWords: string;
  emptyVocabulary: string;
  stats: string;
  pos: string;
  settings: string;
  settingsSubtitle: string;
  interfaceSection: string;
  llmProvider: string;
  generationDefaults: string;
  generationDefaultsHint: string;
  promptTemplate: string;
  dangerZone: string;
  endpoint: string;
  apiKey: string;
  apiKeyPlaceholder: string;
  apiKeyHint: string;
  ollamaLocal: string;
  clearAllVocabulary: string;
  clearAllVocabularyDescription: string;
  clearDatabase: string;
}

const STORAGE_KEY = "openvoca.ui.locale";

export const MESSAGES: Record<Locale, LocaleMessages> = {
  en: {
    menu: "MENU",
    readingDisplaySettings: "Reading display settings",
    loadingSentence: "Asking gemma3:4b for one sentence...",
    ollamaError: "Unable to reach the local Ollama model.",
    feedbackError: "Failed to save your word feedback.",
    provider: "Provider",
    model: "Model",
    targetWordCount: "Words Per Sentence",
    targetWordCountHint:
      "Choose how many review words the model should try to weave into each sentence.",
    resetToDefault: "Reset to default",
    targetWordsTokenHintPrefix: "Use",
    targetWordsTokenHintSuffix:
      "where the menu should inject the selected words.",
    language: "Language",
    fontSize: "Size",
    spacing: "Spacing",
    theme: "Theme",
    themeLight: "Light",
    themeDark: "Dark",
    uiSize: "Interface Size",
    nextSentenceHint: "Hold to continue",
    releaseHint: "Release!",
    vocabulary: "Your Vocabulary",
    backToReading: "Back to Reading",
    clearVocabulary: "Clear All",
    familiarityNeedsReview: "Needs Review",
    familiarityLearning: "Learning",
    familiarityFamiliar: "Familiar",
    familiarityMastered: "Mastered",
    showingWords: "words total",
    emptyVocabulary: "No words yet. Start reading to build your vocabulary.",
    stats: "Stats",
    pos: "POS",
    settings: "Settings",
    settingsSubtitle: "Application configuration and preferences.",
    interfaceSection: "Interface",
    llmProvider: "LLM Provider",
    generationDefaults: "Generation Defaults",
    generationDefaultsHint:
      "These can be overridden per-sentence in the reading view.",
    promptTemplate: "Prompt Template",
    dangerZone: "Danger Zone",
    endpoint: "Endpoint",
    apiKey: "API Key",
    apiKeyPlaceholder: "Not required for local models",
    apiKeyHint:
      "Stored locally on your machine. Never transmitted to third parties.",
    ollamaLocal: "Ollama (Local)",
    clearAllVocabulary: "Clear all vocabulary",
    clearAllVocabularyDescription:
      "Permanently delete all word records and learning progress.",
    clearDatabase: "Clear Database",
  },
  zh: {
    menu: "菜单",
    readingDisplaySettings: "阅读显示设置",
    loadingSentence: "正在向 gemma3:4b 请求一句例句...",
    ollamaError: "无法连接本地 Ollama 模型。",
    feedbackError: "保存词汇反馈失败。",
    provider: "提供商",
    model: "模型",
    targetWordCount: "单轮取词量",
    targetWordCountHint: "决定每一句里尝试塞入多少个复习词，范围 1 到 5。",
    resetToDefault: "恢复默认",
    targetWordsTokenHintPrefix: "在提示词中使用",
    targetWordsTokenHintSuffix: "来注入目标词。",
    language: "语言",
    fontSize: "字号",
    spacing: "间距",
    theme: "主题",
    themeLight: "明亮",
    themeDark: "暗色",
    uiSize: "界面字号",
    nextSentenceHint: "长按进入下一句",
    releaseHint: "松手！",
    vocabulary: "你的词库",
    backToReading: "返回阅读",
    clearVocabulary: "清空词库",
    familiarityNeedsReview: "需复习",
    familiarityLearning: "学习中",
    familiarityFamiliar: "较熟悉",
    familiarityMastered: "已掌握",
    showingWords: "个单词",
    emptyVocabulary: "暂无单词，开始阅读以积累你的词库。",
    stats: "统计",
    pos: "词性",
    settings: "设置",
    settingsSubtitle: "应用配置与偏好。",
    interfaceSection: "界面",
    llmProvider: "模型提供商",
    generationDefaults: "生成默认值",
    generationDefaultsHint: "可在阅读界面中逐句覆盖。",
    promptTemplate: "提示词模板",
    dangerZone: "危险操作",
    endpoint: "端点",
    apiKey: "API 密钥",
    apiKeyPlaceholder: "本地模型无需填写",
    apiKeyHint: "仅存储在本地，不会传输给第三方。",
    ollamaLocal: "Ollama（本地）",
    clearAllVocabulary: "清空所有词汇",
    clearAllVocabularyDescription: "永久删除所有单词记录和学习进度。",
    clearDatabase: "清空数据库",
  },
};

function detectInitialLocale(): Locale {
  // Try settings store (backed by localStorage cache) first
  const { get } = useSettings();
  const stored = get("interface", "locale", "");
  if (stored === "en" || stored === "zh") return stored;

  // Fall back to legacy localStorage key
  if (typeof window !== "undefined") {
    const legacy = window.localStorage.getItem(STORAGE_KEY);
    if (legacy === "en" || legacy === "zh") return legacy;

    const browserLanguage = window.navigator.language.toLowerCase();
    return browserLanguage.startsWith("zh") ? "zh" : "en";
  }

  return "en";
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
