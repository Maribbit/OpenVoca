import { computed, ref } from "vue";

export type Locale = "en" | "zh";

interface LocaleMessages {
  menu: string;
  reading: string;
  readingDisplaySettings: string;
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
  targetWordCount: string;
  targetWordCountHint: string;
  promptEngineering: string;
  resetToDefault: string;
  generationPrompt: string;
  targetWordsTokenHintPrefix: string;
  targetWordsTokenHintSuffix: string;
  menuErrorMissingPrompt: string;
  cancel: string;
  saveChanges: string;
  language: string;
  fontSize: string;
  spacing: string;
  theme: string;
  spacingTight: string;
  spacingNormal: string;
  spacingLoose: string;
  themeLight: string;
  themeDark: string;
  systemFont: string;
  uiFontSans: string;
  uiFontSerif: string;
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
}

const STORAGE_KEY = "openvoca.ui.locale";

export const MESSAGES: Record<Locale, LocaleMessages> = {
  en: {
    menu: "MENU",
    reading: "Reading",
    readingDisplaySettings: "Reading display settings",
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
    targetWordCount: "Words Per Sentence",
    targetWordCountHint:
      "Choose how many review words the model should try to weave into each sentence.",
    promptEngineering: "Prompt Engineering",
    resetToDefault: "Reset to default",
    generationPrompt: "Generation Prompt",
    targetWordsTokenHintPrefix: "Use",
    targetWordsTokenHintSuffix:
      "where the menu should inject the selected words.",
    menuErrorMissingPrompt: "Generation prompt cannot be empty.",
    cancel: "Cancel",
    saveChanges: "Save Changes",
    language: "Language",
    fontSize: "Size",
    spacing: "Spacing",
    theme: "Theme",
    spacingTight: "Tight",
    spacingNormal: "Normal",
    spacingLoose: "Loose",
    themeLight: "Light",
    themeDark: "Dark",
    systemFont: "System Font",
    uiFontSans: "Sans",
    uiFontSerif: "Serif",
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
  },
  zh: {
    menu: "菜单",
    reading: "阅读",
    readingDisplaySettings: "阅读显示设置",
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
    targetWordCount: "单轮取词量",
    targetWordCountHint: "决定每一句里尝试塞入多少个复习词，范围 1 到 5。",
    promptEngineering: "提示词设置",
    resetToDefault: "恢复默认",
    generationPrompt: "生成提示词",
    targetWordsTokenHintPrefix: "在提示词中使用",
    targetWordsTokenHintSuffix: "来注入目标词。",
    menuErrorMissingPrompt: "生成提示词不能为空。",
    cancel: "取消",
    saveChanges: "保存修改",
    language: "语言",
    fontSize: "字号",
    spacing: "间距",
    theme: "主题",
    spacingTight: "紧凑",
    spacingNormal: "标准",
    spacingLoose: "宽松",
    themeLight: "明亮",
    themeDark: "暗色",
    systemFont: "系统字体",
    uiFontSans: "标准 (Sans)",
    uiFontSerif: "阅读 (Serif)",
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
