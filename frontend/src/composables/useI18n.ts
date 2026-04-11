import { computed, ref } from "vue";

import { useSettings } from "./useSettings";

export type Locale = "en" | "zh";

interface LocaleMessages {
  menu: string;
  readingDisplaySettings: string;
  loadingSentence: string;
  connectionError: string;
  feedbackError: string;
  model: string;
  targetWordCount: string;
  targetWordCountHint: string;
  language: string;
  fontSize: string;
  spacing: string;
  theme: string;
  themeLight: string;
  themeDark: string;
  uiSize: string;
  uiSizeHint: string;
  nextSentenceHint: string;
  releaseHint: string;
  vocabulary: string;
  backToReading: string;
  clearVocabulary: string;
  exportVocabulary: string;
  showingWords: string;
  emptyVocabulary: string;
  stats: string;
  pos: string;
  settings: string;
  settingsSubtitle: string;
  interfaceSection: string;
  llmProvider: string;
  llmProviderHint: string;
  testConnection: string;
  testingConnection: string;
  generationDefaults: string;
  dangerZone: string;
  endpoint: string;
  endpointHint: string;
  apiKey: string;
  apiKeyPlaceholder: string;
  apiKeyHint: string;
  modelPlaceholder: string;
  clearAllVocabulary: string;
  clearAllVocabularyDescription: string;
  clearDatabase: string;
  clearAllSettings: string;
  clearAllSettingsDescription: string;
  clearSettingsButton: string;
  dataSection: string;
  exportSettings: string;
  exportSettingsDescription: string;
  exportSettingsButton: string;
  exportVocabularySettings: string;
  exportVocabularySettingsDescription: string;
  exportVocabularySettingsButton: string;
  confirmClearVocabulary: string;
  confirmClearSettings: string;
  composerScenario: string;
  composerScenario_absurd_headlines: string;
  composerScenario_poetry: string;
  composerScenario_fun_facts: string;
  composerScenario_slice_of_life: string;
  composerScenario_none: string;
  composerCustomPlaceholder: string;
  composerCustomPlaceholderSupplement: string;
  composerAddDetails: string;
  composerCustom: string;
  composerNoLimit: string;
  composerCustomDifficultyPlaceholder: string;
  composerCustomLengthPlaceholder: string;
  composerDifficulty: string;
  composerDiffEasy: string;
  composerDiffNormal: string;
  composerDiffChallenge: string;
  composerLength: string;
  composerLenBrief: string;
  composerLenSentence: string;
  composerLenNarrative: string;
  composerGenerate: string;
  composerPreview: string;
  composerTargetWords: string;
  composerTargetWordsHint: string;
  composerAddWordPlaceholder: string;
  statsLemma: string;
  statsInterval: string;
  statsCooldown: string;
  definitionKnow: string;
  definitionDontKnow: string;
  definitionNotFound: string;
  copySentence: string;
  readAloud: string;
  dictionarySection: string;
  dictionaryDisplay: string;
  dictionaryDisplayZh: string;
  dictionaryDisplayEn: string;
  dictionaryDisplayBoth: string;
  intervalHalve: string;
  intervalDouble: string;
  deleteWord: string;
  sortByDue: string;
  sortByFamiliarity: string;
  sortByRecent: string;
  lastSeenLabel: string;
  lastContextLabel: string;
}

const STORAGE_KEY = "openvoca.ui.locale";

export const MESSAGES: Record<Locale, LocaleMessages> = {
  en: {
    menu: "MENU",
    readingDisplaySettings: "Reading display settings",
    loadingSentence: "Generating a sentence…",
    connectionError: "Unable to reach the model. Check your settings.",
    feedbackError: "Failed to save your word feedback.",
    model: "Model",
    targetWordCount: "Words Per Sentence",
    targetWordCountHint:
      "How many review words the model weaves into each sentence. Fewer words = more natural output.",
    language: "Language",
    fontSize: "Size",
    spacing: "Spacing",
    theme: "Theme",
    themeLight: "Light",
    themeDark: "Dark",
    uiSize: "Zoom",
    uiSizeHint:
      "Uses CSS zoom. Requires a modern browser (Chrome 1+, Firefox 126+, Safari 3.1+).",
    nextSentenceHint: "Hold to continue",
    releaseHint: "Release!",
    vocabulary: "Your Vocabulary",
    backToReading: "Back to Reading",
    clearVocabulary: "Clear All",
    exportVocabulary: "Export",
    showingWords: "words total",
    emptyVocabulary: "No words yet. Start reading to build your vocabulary.",
    stats: "Stats",
    pos: "POS",
    settings: "Settings",
    settingsSubtitle: "Application configuration and preferences.",
    interfaceSection: "Interface",
    llmProvider: "Model",
    llmProviderHint:
      "Uses the OpenAI API format (/v1/chat/completions). Compatible with Ollama, OpenRouter, Groq, SiliconFlow, and more.",
    testConnection: "Test Connection",
    testingConnection: "Testing\u2026",
    generationDefaults: "Word Picking",
    dangerZone: "Danger Zone",
    endpoint: "Endpoint",
    endpointHint:
      "Enter the base URL only (e.g. http://localhost:11434). The /v1/chat/completions path is added automatically.",
    apiKey: "API Key",
    apiKeyPlaceholder: "Not required for local models",
    apiKeyHint:
      "Stored locally on your machine. Never transmitted to third parties.",
    modelPlaceholder: "e.g. deepseek-chat, gpt-4o-mini",
    clearAllVocabulary: "Clear all vocabulary",
    clearAllVocabularyDescription:
      "Permanently delete all word records and learning progress.",
    clearDatabase: "Clear Database",
    clearAllSettings: "Clear all settings",
    clearAllSettingsDescription:
      "Reset all preferences (interface, reading, generation, composer) to defaults.",
    clearSettingsButton: "Clear Settings",
    dataSection: "Data",
    exportSettings: "Export settings",
    exportSettingsDescription:
      "Download all settings as a JSON file for backup or migration.",
    exportSettingsButton: "Export JSON",
    exportVocabularySettings: "Export vocabulary",
    exportVocabularySettingsDescription:
      "Download all word records as a CSV file for backup or analysis.",
    exportVocabularySettingsButton: "Export CSV",
    confirmClearVocabulary:
      "Are you sure you want to delete all vocabulary? This cannot be undone.",
    confirmClearSettings:
      "Are you sure you want to reset all settings to defaults? This cannot be undone.",
    composerScenario: "Scenario",
    composerScenario_absurd_headlines: "Fake News",
    composerScenario_poetry: "Poetry",
    composerScenario_fun_facts: "Fun Facts",
    composerScenario_slice_of_life: "Slice of Life",
    composerScenario_none: "Custom",
    composerCustomPlaceholder: "Describe what you want…",
    composerCustomPlaceholderSupplement: "Add details or context…",
    composerAddDetails: "Add details",
    composerCustom: "Custom",
    composerNoLimit: "No limit",
    composerCustomDifficultyPlaceholder: "Describe the difficulty level…",
    composerCustomLengthPlaceholder:
      "Describe the desired length, or leave empty for any…",
    composerDifficulty: "Difficulty",
    composerDiffEasy: "Easy",
    composerDiffNormal: "Normal",
    composerDiffChallenge: "Challenge",
    composerLength: "Length",
    composerLenBrief: "Brief",
    composerLenSentence: "Sentence",
    composerLenNarrative: "Narrative",
    composerGenerate: "Generate next sentence",
    composerPreview: "Preview prompt",
    composerTargetWords: "Target Words",
    composerTargetWordsHint: "auto-selected from vocabulary",
    composerAddWordPlaceholder: "type & enter",
    statsLemma: "Lemma",
    statsInterval: "Familiarity",
    statsCooldown: "Cooldown",
    definitionKnow: "Know",
    definitionDontKnow: "Don't know",
    definitionNotFound: "No definition found",
    copySentence: "Copy sentence",
    readAloud: "Read aloud",
    dictionarySection: "Dictionary",
    dictionaryDisplay: "Definition Language",
    dictionaryDisplayZh: "中文",
    dictionaryDisplayEn: "EN",
    dictionaryDisplayBoth: "Both",
    intervalHalve: "Decrease familiarity",
    intervalDouble: "Increase familiarity",
    deleteWord: "Delete word",
    sortByDue: "Due for Review",
    sortByFamiliarity: "By Familiarity",
    sortByRecent: "By Recent",
    lastSeenLabel: "Last seen",
    lastContextLabel: "Last context",
  },
  zh: {
    menu: "菜单",
    readingDisplaySettings: "阅读显示设置",
    loadingSentence: "正在生成例句…",
    connectionError: "无法连接模型。请检查设置。",
    feedbackError: "保存词汇反馈失败。",
    model: "模型",
    targetWordCount: "单轮取词量",
    targetWordCountHint: "每一句里塞入的复习词数量。越少生成质量越高。",
    language: "语言",
    fontSize: "字号",
    spacing: "间距",
    theme: "主题",
    themeLight: "明亮",
    themeDark: "暗色",
    uiSize: "缩放",
    uiSizeHint:
      "使用 CSS 缩放。需要现代浏览器（Chrome 1+、Firefox 126+、Safari 3.1+）。",
    nextSentenceHint: "长按进入下一句",
    releaseHint: "松手！",
    vocabulary: "你的词库",
    backToReading: "返回阅读",
    clearVocabulary: "清空词库",
    exportVocabulary: "导出词库",
    showingWords: "个单词",
    emptyVocabulary: "暂无单词，开始阅读以积累你的词库。",
    stats: "统计",
    pos: "词性",
    settings: "设置",
    settingsSubtitle: "应用配置与偏好。",
    interfaceSection: "界面",
    llmProvider: "模型配置",
    llmProviderHint:
      "通过 OpenAI API 格式（/v1/chat/completions）调用。兼容 Ollama、OpenRouter、Groq、硅基流动等服务。",
    testConnection: "测试连接",
    testingConnection: "测试中\u2026",
    generationDefaults: "取词策略",
    dangerZone: "危险操作",
    endpoint: "端点",
    endpointHint:
      "只填基础地址（如 http://localhost:11434），/v1/chat/completions 路径会自动拼接。",
    apiKey: "API 密钥",
    apiKeyPlaceholder: "本地模型无需填写",
    apiKeyHint: "仅存储在本地，不会传输给第三方。",
    modelPlaceholder: "如 deepseek-chat、gpt-4o-mini",
    clearAllVocabulary: "清空所有词汇",
    clearAllVocabularyDescription: "永久删除所有单词记录和学习进度。",
    clearDatabase: "清空数据库",
    clearAllSettings: "清空所有设置",
    clearAllSettingsDescription:
      "将所有偏好设置（界面、阅读、生成、编排器）恢复为默认值。",
    clearSettingsButton: "清空设置",
    dataSection: "数据",
    exportSettings: "导出设置",
    exportSettingsDescription: "将所有设置下载为 JSON 文件，用于备份或迁移。",
    exportSettingsButton: "导出 JSON",
    exportVocabularySettings: "导出词库",
    exportVocabularySettingsDescription:
      "将所有单词记录下载为 CSV 文件，用于备份或分析。",
    exportVocabularySettingsButton: "导出 CSV",
    confirmClearVocabulary: "确定要删除所有词汇吗？此操作不可撤销。",
    confirmClearSettings: "确定要恢复所有设置为默认值吗？此操作不可撤销。",
    composerScenario: "场景",
    composerScenario_absurd_headlines: "假新闻",
    composerScenario_poetry: "诗歌",
    composerScenario_fun_facts: "冷知识",
    composerScenario_slice_of_life: "日常",
    composerScenario_none: "自定义",
    composerCustomPlaceholder: "描述你想要的内容…",
    composerCustomPlaceholderSupplement: "添加细节或上下文…",
    composerAddDetails: "添加细节",
    composerCustom: "自定义",
    composerNoLimit: "不限",
    composerCustomDifficultyPlaceholder: "描述难度要求…",
    composerCustomLengthPlaceholder: "描述长度要求，留空则不限…",
    composerDifficulty: "难度",
    composerDiffEasy: "简单",
    composerDiffNormal: "普通",
    composerDiffChallenge: "挑战",
    composerLength: "长度",
    composerLenBrief: "短句",
    composerLenSentence: "标准句",
    composerLenNarrative: "长句",
    composerGenerate: "生成下一句",
    composerPreview: "预览提示词",
    composerTargetWords: "目标词",
    composerTargetWordsHint: "从词库自动选取",
    composerAddWordPlaceholder: "输入并回车",
    statsLemma: "词元",
    statsInterval: "熟悉度",
    statsCooldown: "冷却剩余",
    definitionKnow: "认识",
    definitionDontKnow: "不认识",
    definitionNotFound: "未找到释义",
    copySentence: "复制句子",
    readAloud: "朗读",
    dictionarySection: "词典",
    dictionaryDisplay: "释义语言",
    dictionaryDisplayZh: "中文",
    dictionaryDisplayEn: "EN",
    dictionaryDisplayBoth: "双语",
    intervalHalve: "降低熟悉度",
    intervalDouble: "提高熟悉度",
    deleteWord: "删除词条",
    sortByDue: "即将复习",
    sortByFamiliarity: "按熟悉度",
    sortByRecent: "按最近复习",
    lastSeenLabel: "上次复习",
    lastContextLabel: "上次例句",
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
