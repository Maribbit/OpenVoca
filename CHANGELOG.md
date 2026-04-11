# Changelog

All notable changes to this project will be documented in this file.

## v0.7.4

Date: 2026-04-12

### New Features
- **Vocabulary import** — Import vocabulary from a CSV file via the Stats page. The endpoint accepts the same four-column format (`lemma`, `pos`, `interval`, `cooldown`) used by export, with row-level validation, case normalization, value clamping, and a 5 000-row / 1 MB limit.
- **Import mode (skip / overwrite)** — By default, importing preserves existing learning progress (skip mode). When existing words are detected, a contextual "Overwrite" button appears in the result banner, letting users re-import with overwrite mode without selecting the file again.
- **External dictionary links** — DefinitionToast now shows quick links to Merriam-Webster, Cambridge, and Youdao below the definition for further lookup.

### Improvements
- **i18n for import messages** — All import result messages (success, partial, failure) are fully localized in English and Chinese.

### Changed Files
- `backend/src/main.py`: new `POST /api/vocabulary/import` endpoint (multipart CSV + `mode` form field).
- `backend/src/services/word_store.py`: `ImportResult` dataclass, `import_vocabulary()` with skip/overwrite mode.
- `frontend/src/api/reading.ts`: `importVocabulary(file, mode)` API helper.
- `frontend/src/views/StatsView.vue`: import button, file input, result banner with contextual overwrite action.
- `frontend/src/components/DefinitionToast.vue`: external dictionary links (MW, Cambridge, Youdao).
- `frontend/src/composables/useI18n.ts`: new i18n keys for import-related messages.
- `backend/tests/test_word_store.py`, `backend/tests/test_main.py`: 19 new import tests.

---

## v0.7.3

Date: 2026-04-11

### Bug Fixes
- **Firefox line-wrap fix** — Sentences no longer overflow horizontally in Firefox. Two root causes were addressed:
  1. Vue's template compiler (condensed whitespace mode) was stripping the space text node inside `<span> </span>`, leaving no line-break opportunities between word spans. The space is now rendered via `{{ ' ' }}` mustache interpolation inside a `<template>` element, which compiles to `createTextVNode(' ')` unconditionally.
  2. The `<article>` flex item had `min-width: auto` (the flex default), which resolved to the sentence's full one-line width because each word span carries `whitespace-nowrap`. Added `min-w-0` to allow the flex item to shrink and text to wrap.

### Other
- **`.gitignore`** — Added `build/` and `dist/` entries (bundle script output directories were previously untracked).
- **README** — New "Building a Release Package (Windows)" section documents prerequisites, the `uv run python scripts/bundle.py` command, the 8-step build process, and a note on automatic dependency management via `uv.lock`.

### Changed Files
- `frontend/src/components/SentenceDisplay.vue`: space span replaced with `<template>{{ ' ' }}</template>`; `min-w-0` added to `<article>`.
- `.gitignore`: added `build/` and `dist/`.
- `README.md`: added build instructions section.

---

## v0.7.2

Date: 2026-04-12

### Highlights
- **First-run experience** — Generation failures no longer strand the user on a blank reading view. The Composer stays visible and an inline error banner with a direct "Go to Settings →" link appears below the card.
- **Target Words redesign** — Suggestion chips (from vocabulary) are now toggleable (click to deselect/reselect) and never permanently destroyed. User-typed custom words are visually distinct (lighter fill + ×). A ↺ refresh button lets users fetch a fresh pool without reloading the page.
- **Word Picking settings split** — The single "Words Per Sentence" slider is now two linked sliders: **Suggestion Pool** (how many chips appear, 1–6) and **Auto-selected** (how many start pre-selected, 0–pool). Reducing the pool automatically clamps the auto-select value.
- **Language detection fixed** — A stale legacy `localStorage` key (`openvoca.ui.locale`) was shadowing `navigator.language` after clearing settings. The legacy key has been removed entirely; locale now persists exclusively through the settings store.
- **UI language order** — English moved to the left in the language picker (Settings → Interface). Dictionary display order changed to EN | Both | 中文.
- **Smart dictionary default** — First-run default for definition language is now browser-detection-aware: **EN** for non-Chinese browsers, **Both** for Chinese browsers (applies to Settings picker and the reading view).

### Frontend
- `HomeView.vue`: on generation error, `showComposer` is reverted to `true`; new `composerError` ref drives an inline error banner below `ComposerCard` with a `router-link` to `/settings`.
- `ComposerCard.vue`:
  - Data model split into `suggestedWords`, `activeSuggestions` (Set), and `customWords`. `effectiveTargetWords` computed combines active suggestions + custom words.
  - `loadTargetWords()` now reads `generation.suggestionPoolSize` (pool fetch count) and `generation.targetWordCount` (auto-select count separately) — first `autoSelect` fetched words are pre-activated.
  - Template: suggestion chips use new `.suggestion-chip.active/.inactive` styles (toggleable, no × button); custom chips use `.custom-chip` (lighter fill, × to remove); refresh button replaces the hint text in the header.
  - Scoped CSS updated: `.word-chip` removed, `.suggestion-chip` and `.custom-chip` added.
- `SettingsView.vue`:
  - Added `draftSuggestionPoolSize` ref (reads `generation.suggestionPoolSize`, default 3).
  - Word Picking section replaced with two sliders; auto-select slider `max` is bound to pool size; pool-change watch clamps auto-select.
  - Language picker: English button moved left.
  - Dictionary display order changed to EN | Both | 中文; default now inferred from `navigator.language`.
- `useI18n.ts`:
  - Removed legacy `STORAGE_KEY` constant and all `localStorage.setItem/getItem` calls for locale — persistence is now via settings store only.
  - `targetWordCount` label/hint updated to describe auto-select semantics.
  - Added `suggestionPoolSize` / `suggestionPoolSizeHint` keys.
  - Added `goToSettings` key ("Go to Settings →" / "前往设置 →").
  - Renamed `composerTargetWordsHint` → `composerRefreshSuggestions`.
- `HomeView.vue`: `dictionaryDisplayMode` default changed from hardcoded `"both"` to browser-language-aware detection.
- Tests: locale-persistence test updated to assert via `openvoca.settings.cache` instead of deleted `openvoca.ui.locale` key.

### Design
- `ui_guide_composer_light.html` and `ui_guide_composer_dark.html`: Target Words section updated to show two-zone chip design (toggleable suggestions + custom chips with ×, ↺ refresh button).

---

## v0.7.1

Date: 2026-04-11

### Highlights
- **Static file serving fix** — `GET /` now serves the Vue SPA (`index.html`) in production. The health check was renamed to `GET /api/health` so routing no longer conflicts.
- **Composer UI polish** — Section dividers removed (spacing-only rhythm), scenario card background unified, and the scenario supplement textarea replaced with a `+ Add details` expand button, preserving access while keeping the default view clean.
- **Fake News prompt revised** — Removed disaster-biased language (`crisis`, `breaking news`); now explicitly lists diverse beats (science, culture, sports, weather, economics) for varied output.

### Backend
- `main.py`: health endpoint moved from `GET /` to `GET /api/health`. Added `GET /` (`serve_root`) to the SPA section so the root URL serves the frontend.
- `test_main.py`: `test_read_root` renamed to `test_health_endpoint`, path updated to `/api/health`.

### Frontend
- `ComposerCard.vue`:
  - Section `border-t` dividers removed; card spacing increased to `space-y-6`.
  - Scenario cards background changed from `paper` to `surface` (matches option-cards in Difficulty/Length).
  - Supplement textarea replaced with `+ 添加细节` expand button for preset scenarios; textarea auto-shows for "自定义" or when the user has existing content. Scenario switching resets the open state when content is empty.
  - `absurd_headlines` prompt revised: removed `crisis` / `breaking news`; added explicit beat list (`local news, science, culture, sports, weather, economics`).
  - Poetry scenario emoji changed `✏️` → `📜`; "无预设" renamed to "自定义" / "No Preset" → "Custom".
- `useI18n.ts`: added `composerAddDetails` key (`"Add details"` / `"添加细节"`).

### Design
- `ui_guide_composer_dark.html` and `ui_guide_composer_light.html` updated to reflect all composer changes: scenario card backgrounds, expand-button pattern for supplement input, poetry emoji, "Custom" naming, divider removal, `space-y-6` spacing.

### Breaking Changes
- `GET /` no longer returns the JSON health response — use `GET /api/health` instead. (Only affects direct API consumers; the frontend was not using this endpoint.)

---

## v0.7.0

Date: 2025-04-10

### Highlights
- **Phase A — Portable distribution foundation** — The backend now serves the compiled frontend as static files, eliminating the need to run a separate Vite dev server for production use. Mount and SPA fallback are conditional (only active when `frontend/dist` exists), so the existing dev workflow is unaffected.
- **Data directory isolation** — A new `OPENVOCA_DATA_DIR` environment variable controls where `openvoca.db` is written. When set, the database is created at `$OPENVOCA_DATA_DIR/openvoca.db`; otherwise it defaults to `./openvoca.db` as before. This is the foundation for the v0.7.0 portable ZIP distribution.
- **Test file reorganization** — Backend test suite split into focused files: `test_main.py` (HTTP API), `test_word_store.py` (storage + engine), `test_tokenizer.py` (tokenizer), `test_static.py` (SPA serving), reducing `test_main.py` from 648 to ~560 lines and removing duplicate tokenizer tests.
- **Open-source license** — Project is now licensed under **AGPL-3.0**. `LICENSE` file, `README.md` license section, and `CONTRIBUTING.md` contributor notice added.

### Backend
- `word_store.py`: `_make_engine()` function added. Reads `OPENVOCA_DATA_DIR` env var for the DB path; `_engine` is initialized via this function (monkeypatchable).
- `main.py`: imports reorganized (alphabetical); `StaticFiles` mount + `spa_fallback` route added at end of file. Both are conditional on `frontend/dist` existing at startup.
- New test file `test_static.py`: verifies `spa_fallback()` returns `FileResponse` pointing at `index.html`.
- `test_word_store.py`: 2 new tests for `_make_engine()` (default path + `OPENVOCA_DATA_DIR`).
- 2 duplicate tokenizer tests removed from `test_main.py`. Total: **107 backend tests**.

### Frontend
- Version bump only (`0.7.0`). No functional changes.

### Design
- `design/Bundling.md` added — comprehensive portable distribution design (ZIP, Rust launcher, tray icon, update strategy, Phases A–D).

### Breaking Changes
- None. `OPENVOCA_DATA_DIR` is opt-in; defaults unchanged.

---

## v0.6.10

Date: 2026-04-09

### Highlights
- **Default zoom reset** — default UI zoom changed from 125% back to 100% for a more natural initial experience.
- **Dark mode button fix** — Tailwind `dark:` variant now scoped to `data-reading-theme="dark"` instead of OS `prefers-color-scheme`, fixing invisible button borders when the OS is in dark mode but the app is in light mode.
- **Three-way vocabulary sort** — Stats page now offers three sort modes: "Due for Review" (cooldown ASC), "By Familiarity" (interval ASC — least familiar first), and "By Recent" (last seen DESC). Previously "By Familiarity" was actually sorting by cooldown.
- **Familiarity progress bar** — replaced the color dot in the interval column with a horizontal progress bar using a logarithmic scale (2→64), making learning progress more intuitive at a glance.
- **Terminology cleanup** — column header and button titles renamed from "Interval"/"复习间隔" to "Familiarity"/"熟悉度" for consistency.

### Backend
- `list_all_words()` in `word_store.py`: default sort renamed from `"familiarity"` to `"due"` (cooldown ASC, interval ASC). New `"familiarity"` mode sorts by interval ASC, cooldown ASC.
- `GET /api/vocabulary`: query parameter `sort` now accepts `due|familiarity|recent` (was `familiarity|recent`), default changed to `due`.
- 1 new test (`test_vocabulary_sort_familiarity`), 1 renamed test (`test_vocabulary_sort_due`). Total: 106 backend tests.

### Frontend
- `main.css`: added `@variant dark` override to scope `dark:` utilities to `[data-reading-theme="dark"]`.
- `App.vue` / `SettingsView.vue`: default zoom changed from `"md"` (125%) to `"sm"` (100%).
- `SettingsView.vue`: button border opacity increased from `border-black/10` to `border-black/15`.
- `StatsView.vue`: three sort pills (Due for Review / By Familiarity / By Recent), default `"due"`. Interval column shows progress bar instead of number + label + dot. Removed `intervalLabel()` function.
- `reading.ts`: `fetchVocabulary()` accepts `"due" | "familiarity" | "recent"`, default `"due"`.
- `useI18n.ts`: added `sortByDue` key (EN: "Due for Review", ZH: "即将复习"). Renamed `statsInterval` to "Familiarity"/"熟悉度". Updated `intervalHalve`/`intervalDouble` titles. Removed 4 dead keys (`familiarityNeedsReview`, `familiarityLearning`, `familiarityFamiliar`, `familiarityMastered`).
- 11 frontend tests passing.

### Breaking Changes
- `GET /api/vocabulary` default sort changed from `familiarity` to `due`. The old `?sort=familiarity` still works but now sorts by interval ASC instead of cooldown ASC.

---

## v0.6.9

Date: 2026-04-06

### Highlights
- **Zoom viewport fix** — views at zoom levels above 100% no longer produce a scrollbar or break vertical centering. A new `--app-zoom` CSS custom property drives a `min-h-zoom-screen` utility that compensates `100vh` for the active zoom factor.
- **Dark mode button contrast** — "Test Connection", "Export CSV", and "Export JSON" buttons in Settings now have visible borders and hover states in dark mode (`dark:border-white/15`, `dark:hover:bg-white/8`).

### Frontend
- `App.vue` / `SettingsView.vue`: `applyZoom()` now sets `--app-zoom` CSS variable alongside `zoom` on `#app`.
- `main.css`: added `.min-h-zoom-screen { min-height: calc(100vh / var(--app-zoom, 1)); }` utility.
- `HomeView.vue`, `StatsView.vue`, `SettingsView.vue`: replaced `min-h-screen` with `min-h-zoom-screen`.
- `SettingsView.vue`: added `dark:border-white/15 dark:hover:bg-white/8` to three action buttons.

---

## v0.6.8

Date: 2026-04-06

### Highlights
- **Stats page: sortable vocabulary** — two sort modes via pill toggle: "By Familiarity" (cooldown ASC, interval ASC) and "By Recent" (last reviewed first). Sorting is performed server-side for future pagination readiness.
- **Stats page: expandable word details** — click any row to reveal the last review timestamp (relative, e.g. "3h ago") and the previous sentence context in which the word appeared.
- **Dark mode fix** — the "Know" button in the definition toast is now readable in dark mode (was white-on-white).
- **Timezone fix** — `lastSeen` timestamps are now always serialized with a UTC offset (`+00:00`), preventing local-time misinterpretation on the frontend.
- **Progress bar removed** — the non-functional decorative progress bar at the top of the reading view has been removed from both the Vue code and design mockups.

### Backend
- `WordRecordOut` response model now includes `lastSeen` (ISO 8601 with UTC offset).
- `GET /api/vocabulary` accepts `?sort=familiarity|recent` query parameter (validated, 422 on invalid values).
- `list_all_words()` in `word_store.py` accepts `sort` keyword argument for server-side ordering.
- New `_utc_iso()` helper in `main.py` to re-attach UTC timezone to naive datetimes from SQLite.
- 4 new tests: sort familiarity, sort recent, sort invalid, lastSeen presence. Total: 105 backend tests.

### Frontend
- `fetchVocabulary(sort)` in `reading.ts` passes sort mode to backend API.
- `StatsView.vue`: sort toggle pills re-fetch from backend; click any row to expand inline detail showing relative last-seen time and italic previous context. Interactive controls use `.stop` to avoid accidental row toggle.
- `DefinitionToast.vue`: "Know" active button uses `dark:text-black` instead of `dark:text-ink` for readability.
- `HomeView.vue`: removed decorative progress bar div.
- `useI18n.ts`: 4 new i18n keys (`sortByFamiliarity`, `sortByRecent`, `lastSeenLabel`, `lastContextLabel`).
- `WordRecordOut` interface updated with `lastSeen` field.
- Total: 11 frontend tests.

---

## v0.6.7

Date: 2026-04-06

### Highlights
- **Copy & read aloud**: two new action buttons below the sentence — copy to clipboard (with checkmark feedback) and browser TTS read-aloud (with stop toggle).
- **Editable vocabulary records**: interval can be halved (÷2) or doubled (×2) via buttons in the Stats table. Cooldown is now an inline editable number input. Both are clamped to valid ranges.
- **Delete individual words**: each row in the Stats table has a delete button (×) to remove a single word record.
- **Click-to-toggle mark**: clicking the same word again while its definition toast is showing toggles between "Know" and "Don't know" without needing to reach the toast buttons.
- **Stale record safety**: PATCH and DELETE endpoints return 404 when the target record has already been deleted (multi-tab scenario), with dedicated test coverage.

### Backend
- New `PATCH /api/vocabulary/{lemma}/{pos}` endpoint — update interval (clamped to [2, 64]) and/or cooldown (clamped to [0, interval]).
- New `DELETE /api/vocabulary/{lemma}/{pos}` endpoint — remove a single word record; returns 404 if already deleted.
- New `update_word_record()` and `delete_word_record()` functions in `word_store.py`.
- 14 new tests (5 update, 4 delete, 2 API PATCH, 3 API DELETE including stale-tab scenarios). Total: 101 backend tests.

### Frontend
- New `tokensToPlainText()` utility in `reading.ts` — pure function to reconstruct plain text from tokens (6 tests in `reading.spec.ts`).
- New `updateWordRecord()` and `deleteWordRecord()` API functions in `reading.ts`.
- `HomeView.vue`: copy button (clipboard → checkmark for 1.5s) and read-aloud button (speaker → stop square while playing). TTS auto-cancels on sentence advance. Clicking the same word again toggles know/don't-know.
- `StatsView.vue`: interval gets −/+ buttons (exponential ÷2/×2), cooldown is an inline editable `<input type="number">`, each row gets a delete (×) button. Color dot moved after the familiarity label.
- `useI18n.ts`: added 5 new i18n keys (`copySentence`, `readAloud`, `intervalHalve`, `intervalDouble`, `deleteWord`).
- Total: 11 frontend tests (6 reading + 5 HomeView).

---

## v0.6.6

Date: 2026-04-06

### Highlights
- **Hyphenated word merging**: compound words like "lo-fi", "well-known", and "state-of-the-art" are now treated as single clickable tokens instead of being split into separate parts by spaCy.
- **Dictionary default changed to bilingual**: the definition language setting now defaults to "Both" (Chinese + English) instead of Chinese only.

### Backend
- New `_merge_hyphenated()` post-processing pass in `tokenizer.py` — after spaCy tokenization, adjacent `word-hyphen-word` sequences with no intervening whitespace are merged back into a single `SentenceToken`.
- Target matching updated: hyphenated targets like `*lo-fi*` are stored as whole keys, matching merged tokens directly.
- 2 new tests: `test_hyphenated_non_target_word`, `test_hyphenated_chain`. Updated `test_hyphenated_target_word` for merged behavior. Total: 87 backend tests.

### Frontend
- `SettingsView.vue` / `HomeView.vue`: dictionary display default changed from `"zh"` to `"both"`.

---

## v0.6.5

Date: 2026-04-06

### Highlights
- **Built-in dictionary**: click any word in the reading view to see its definition in a top-center toast. Powered by a compact 7.7 MB dictionary extract (ECDICT, 36,896 words).
- **Know / Don't know toggle**: the definition toast includes a toggle — tap "Don't know" to highlight the word, or "Know" (default) to leave it unmarked.
- **Definition language setting**: new "Dictionary" section in Settings lets you choose Chinese only, English only, or both definitions.
- **Multi-line definitions**: long definitions are split by line breaks and capped at 4 lines per language for readability.
- **Word-not-found handling**: words not in the dictionary still show a toast with the word and a "No definition found" message.

### Backend
- New `GET /api/dictionary/{word}` endpoint — case-insensitive lookup returning word, phonetic, definition, translation, pos, tag, exchange. Returns 404 for unknown words.
- New `src/services/dictionary.py` with `lookup()` and `lookup_custom()` functions backed by SQLite.
- New `backend/data/dictionary.db` — compact dictionary extracted from ECDICT (BNC/COCA top 30k + exam-tagged words with Chinese translations).
- New `scripts/extract_dictionary.py` for regenerating the dictionary from `stardict.db`.
- 7 new tests in `test_dictionary.py`. Total: 85 backend tests.

### Frontend
- New `DefinitionToast.vue` component — fixed top-center toast with slide-down animation, definition display, and know/don't-know toggle.
- `SentenceDisplay.vue`: click events now emit `word-click` (replaced `toggle-mark`). Word marking is handled by the toast toggle instead of direct clicks.
- `HomeView.vue`: wired dictionary lookup on word click, document click to dismiss, definition state management. Dismisses toast on sentence advance and composer return.
- `SettingsView.vue`: new "Dictionary" section with definition language toggle (中文 / EN / Both), stored in `dictionary.display` setting.
- `reading.ts`: new `fetchDefinition(word)` API function and `DictionaryEntry` interface.
- `useI18n.ts`: added 8 new i18n keys (`definitionKnow`, `definitionDontKnow`, `definitionNotFound`, `dictionarySection`, `dictionaryDisplay`, `dictionaryDisplayZh`, `dictionaryDisplayEn`, `dictionaryDisplayBoth`).

### Design
- Updated `ui_guide_reading_light.html` and `ui_guide_reading_dark.html` with top-center definition toast mockup.

---

## v0.6.4

Date: 2026-04-06

### Highlights
- **Vocabulary CSV export**: new "Export Vocabulary" button in both the Stats page and the Settings Data section. Downloads all word records as a CSV file (`lemma, pos, interval, cooldown`).
- **Settings page restructured**: the "Data" section (export vocabulary + export settings) now sits above the "Danger Zone" for a more logical flow.
- **Danger Zone confirmation**: "Clear Database" and "Clear Settings" now require explicit confirmation via a browser dialog before executing, preventing accidental data loss.
- **Header UX polish**: removed hover backgrounds from Menu/Stats buttons; moved the settings gear icon next to the Menu link for consistency.
- **Test suite reorganized**: `test_main.py` split into `test_main.py` (API endpoints), `test_word_store.py` (algorithm logic), and `test_openai_compat.py` (LLM client). Shared helper in `conftest.py`. 78 backend tests, 5 frontend tests.

### Backend
- New `GET /api/vocabulary/export` endpoint — returns a streaming CSV response with `Content-Disposition: attachment`.
- 2 new tests: `test_export_vocabulary_csv`, `test_export_vocabulary_csv_empty`.

### Frontend
- `StatsView.vue`: replaced "Clear All" button with "Export" button (CSV download via blob).
- `SettingsView.vue`: added "Export Vocabulary" row to Data section; Data section moved above Danger Zone; both Danger Zone actions now use `window.confirm()`.
- `reading.ts`: new `exportVocabulary()` API function.
- `useI18n.ts`: added 7 new i18n keys (`exportVocabulary`, `exportVocabularySettings`, `exportVocabularySettingsDescription`, `exportVocabularySettingsButton`, `confirmClearVocabulary`, `confirmClearSettings`).

---

## v0.6.3

Date: 2026-04-06

### Highlights
- **Prompt assembly moved to frontend**: the frontend now builds the complete prompt (template interpolation + scenario/difficulty/length instructions + target words). The backend receives a single `prompt` string and only appends the internal markdown-marking directive. This eliminates duplication between preview and generation.
- **Simplified API**: `POST /api/reading-sentence/next` now accepts `{ prompt, targetWords }` instead of `{ promptTemplate, targetWords, composerInstructions }` — 2 fields instead of 3.
- **Backend sorting**: vocabulary list sorting moved from frontend to backend SQL (`ORDER BY cooldown ASC, interval ASC`), preparing for future pagination and filtering.

### Backend
- `prompt_builder.py`: simplified from 50 to 28 lines. No longer does template interpolation or composer instruction concatenation — only appends the IMPORTANT markdown-marking directive when target words are present.
- `ReadingSentenceRequest`: replaced `promptTemplate` + `composerInstructions` with a single `prompt` field. `targetWords` retained for tokenizer marking.
- `list_all_words()`: now sorts by `cooldown ASC, interval ASC` in SQL (was `interval ASC, last_seen ASC`).
- 76 backend tests passing (prompt_builder tests simplified from 9 to 6).

### Frontend
- `ComposerCard.vue`: new `buildPrompt()` function assembles the complete prompt (resolves `{{target_words}}`, appends composer instructions). Emits `(prompt, targetWords)` instead of `(composerInstructions, targetWords)`.
- `HomeView.vue`: removed `DEFAULT_READING_PREFERENCES` import (no longer needed). `loadSentence` sends `{ prompt, targetWords }`.
- `StatsView.vue`: removed client-side sort (backend handles it).

### Breaking Changes
- `POST /api/reading-sentence/next`: request body changed from `{ promptTemplate, targetWords, composerInstructions? }` to `{ prompt, targetWords }`. The `prompt` field must contain the fully assembled prompt.

---

## v0.6.2

Date: 2026-04-06

### Highlights
- **Target Word Preview & Edit**: users can now see, remove, and add target words in the Composer before generating a sentence. Words are auto-selected from the vocabulary and injected into the prompt template.
- **Cooldown tick fix**: `tick_cooldowns()` moved from the preview endpoint to `/api/reading-sentence/next`, preventing repeated page refreshes from draining cooldowns to zero.

### Backend
- New `GET /api/target-words?limit=K` endpoint — picks available words without ticking cooldowns.
- `POST /api/reading-sentence/next` now requires `targetWords: string[]` in the request body (replacing the old `targetWordCount`). Backend uses the frontend-chosen word list directly.
- `tick_cooldowns()` moved back to `/next` — called once per generation cycle, not on preview.
- 2 new tests: `test_target_words_endpoint_does_not_tick`, `test_next_endpoint_ticks_cooldowns`. 79 total backend tests.

### Frontend
- New `fetchTargetWords(limit)` API function.
- `ComposerCard.vue`: fetches target words on mount, displays word chips with `×` remove, `+` button reveals inline input for manual word entry. Target Words section placed at top of card.
- Prompt preview now resolves `{{target_words}}` with the actual selected words.
- `ComposerCard` emits both `composerInstructions` and `targetWords`.
- `StatsView.vue`: words sorted by review priority (cooldown ASC, interval ASC). Table split into 4 columns: Lemma, POS, Interval, Cooldown — matching the database schema.
- New i18n keys: `composerTargetWords`, `composerTargetWordsHint`, `composerAddWordPlaceholder`, `statsLemma`, `statsInterval`, `statsCooldown` (EN + ZH).

### Design Documents
- `ui_guide_composer_light.html` / `ui_guide_composer_dark.html`: fully rewritten with 5-card scenario grid, collapsible sections, Target Words module at top.

### Breaking Changes
- `POST /api/reading-sentence/next`: `targetWordCount` field replaced by `targetWords: string[]`. Clients must now supply an explicit word list.

---

## v0.6.1

Date: 2026-04-06

### Highlights
- **Persistent HTTP connections**: the LLM client now creates a single `httpx.AsyncClient` at init and reuses it across all requests, eliminating per-call connection overhead. Graceful shutdown via FastAPI `lifespan`.
- **SQL-optimized bulk operations**: `tick_cooldowns()` and `clear_all_words()` replaced ORM loops with single raw SQL statements for O(1) database round-trips.
- **Composer UI guide refresh**: both light and dark HTML mockups fully rewritten to match the current implementation — 5-card scenario grid, collapsible difficulty/length with custom, prompt preview, and new Target Words preview module.

### Backend
- `OpenAICompatibleClient`: refactored from per-call `async with httpx.AsyncClient(...)` to persistent client created in `__init__`. Added `aclose()` method.
- FastAPI app: added `lifespan` async context manager that calls `llm.aclose()` on shutdown.
- `set_provider()` is now `async` — closes the old client before creating a new one to prevent connection leaks.
- `word_store.py`: `tick_cooldowns()` now uses `UPDATE wordrecord SET cooldown = cooldown - 1 WHERE cooldown > 0` (single SQL). `clear_all_words()` uses `DELETE FROM wordrecord` with `result.rowcount`.
- Added `from sqlalchemy import text` import for raw SQL execution.
- 2 new tests: persistent connection reuse, graceful client shutdown. 78 total backend tests passing.

---

## v0.6.0

Date: 2026-04-01

### Highlights
- **Scenario-driven Composer**: replaced the Topic + Tone + Length slider with a card-based scenario selector. 4 creative presets (Slice of Life, Fun Facts, Absurd Headlines, Poetry) + a No Preset option, each with a full "persona prompt" injected into the LLM request.
- **Custom Difficulty & Length**: Difficulty and Length panels now collapse by default and each offer 3 presets + a "Custom" option with free-text input. Empty custom = no constraint.
- **Unified model configuration**: replaced the Ollama-specific provider with a generic OpenAI-compatible API client (`/v1/chat/completions`), supporting Ollama, OpenAI, DeepSeek, Groq, OpenRouter, SiliconFlow, and any compatible endpoint.
- **Prompt architecture overhaul**: prompt assembly (scenario + difficulty + length) moved entirely to the frontend. Backend receives the assembled `composerInstructions` string.
- **Dead code housecleaning**: removed legacy `OllamaClient`, `GET /api/models` stub, unused `target_words` request field, and 12 dead i18n keys.

### Breaking Changes
- `GET /api/models` endpoint removed (was already a deprecated stub returning `[]`).
- `target_words` / `targetWords` field removed from `POST /api/reading-sentence/next` request body.
- `OllamaClient` removed. Use `OpenAICompatibleClient` (set endpoint to `http://localhost:11434` for Ollama).

---

## v0.5.1

Date: 2026-03-31

### Highlights
- **Persistent settings store**: all user preferences (interface, reading, generation) are now stored in the backend SQLite database via a new `SettingRecord` model, replacing scattered `localStorage` keys.
- **Settings page refactor**: replaced the modal-based preferences dialog with a full-page `/settings` route, aligning with the `ui_guide_settings.html` design spec.
- **Unified settings composable**: new `useSettings()` reactive singleton provides `get`/`set`/`hydrate` API with instant localStorage cache and async backend sync.

---

## v0.5.0

Date: 2026-03-28

### Highlights
- **Cooldown queue algorithm**: replaced the 0–4 `familiarity` scale with an `interval` + `cooldown` dual-field model. Miss → interval halves; Hit → interval doubles. Words enter a cooldown countdown after each review, emerging automatically when due.
- **Lemma normalization**: vocabulary now keys on `(lemma, pos)` instead of `(word, pos)`. All inflected forms collapse into a single record.
- **`last_context` field**: each word record stores the most recent sentence it appeared in.

### Breaking Changes
- **Database incompatible**: `openvoca.db` must be deleted and recreated. Schema changed from `(word, pos, familiarity, last_seen)` to `(lemma, pos, interval, cooldown, last_seen, last_context)`.
- **API contract changed**: `/api/feedback` now expects `{ lemma, pos }` instead of `{ word, pos }`. `/api/vocabulary` returns `{ lemma, pos, interval, cooldown, lastContext }` instead of `{ word, pos, familiarity }`.

---

## v0.4.9

Date: 2026-03-27

### Added
- Error handling for `submitFeedback`: a 4-second auto-dismissing toast warns when word feedback fails to save.

---

## v0.4.8

Date: 2026-03-27

### Removed
- Dead code: `POST /api/reading-sentence` endpoint, `fetchReadingSentence()` frontend function, and Pinia dependency.

### Breaking Changes
- `POST /api/reading-sentence` removed. Use `POST /api/reading-sentence/next` instead.

---

## v0.4.7

Date: 2026-03-27

### Highlights
- **Component extraction**: split 998-line `HomeView.vue` into `SentenceDisplay`, `HoldButton`, `ReadingSettingsBar`, `PreferencesModal`.
- **LLM abstraction**: introduced `LLMProvider` protocol in the backend, decoupling routes from the Ollama client.

---

## v0.4.6 – v0.4.1

Date: 2026-03-27

### Summary
A series of incremental improvements:
- v0.4.6: Contraction display spacing via `trailingSpace` token flag.
- v0.4.5: Extracted `_generate_reading_response` helper (DRY).
- v0.4.4: Added `lemma` field to tokens; POS-aware word marking in frontend.
- v0.4.3: Fixed hyphenated target words (`*well-known*`); added missing endpoint tests.
- v0.4.2: Replaced static stopword list with POS-aware function-word filtering.
- v0.4.1: Unified tokenization pipeline using spaCy; composite `(word, pos)` primary key.

---

## v0.4.0

Date: 2026-03-23

### Highlights
- Added backend stop-word filtering.
- Preserved model-driven target-word behavior using Markdown markers.
- Phase 1 objective reached: full loop (pick words → generate → mark → update familiarity) is stable.

---

## v0.3.3

Date: 2026-03-23

### Added
- Model-driven target-word annotation using Markdown emphasis markers (`*word*`).
- Sentence highlighting resilient to inflections, synonyms, and empty target-word cases.

---

## v0.3.2

Date: 2026-03-23

### Added
- Configurable per-sentence review word count (1–5) in Preferences.

---

## v0.3.1

Date: 2026-03-22

### Added
- Interface font-size control; dotted underlines for target words in sentence rendering.
- Improved hold-to-continue affordance with centered capsule interaction.

---

## v0.3.0

Date: 2026-03-22

### Highlights
- **Core learning loop**: mark words in-context, submit feedback, update familiarity, generate next sentence from least-familiar words.
- **Vocabulary stats page** with familiarity levels and clear-all support.
- **Hold-to-confirm** interaction for advancing sentences.

---

## v0.2.0

Date: 2026-03-22

### Added
- Tokenization service; `POST /api/reading-sentence` returns tokenized output.
- Inline reading settings panel (size/spacing/theme).
- Reading theme support (light/dark).

### Breaking Changes
- `POST /api/reading-sentence` response now includes a `tokens` field.

---

## v0.1.0

Date: 2026-03-22

### Highlights
- Initial release. Phase 1 minimal closed loop for sentence generation with local Ollama (`gemma3:4b`).
- Reading page with Zen-style layout.
- Preferences menu (target words, prompt template).
- Lightweight i18n (zh/en) with locale persistence.
