import { reactive } from "vue";

import {
  deleteAllSettings,
  fetchAllSettings,
  putNamespace,
  type SettingsMap,
} from "../api/settings";

const CACHE_KEY = "openvoca.settings.cache";

/** Flat reactive store: settings[namespace][key] = value */
const store = reactive<SettingsMap>({});

let hydrated = false;

// --- localStorage cache ---

function loadCache(): SettingsMap {
  if (typeof window === "undefined") return {};
  const raw = window.localStorage.getItem(CACHE_KEY);
  if (!raw) return {};
  try {
    return JSON.parse(raw) as SettingsMap;
  } catch {
    return {};
  }
}

function saveCache(): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(CACHE_KEY, JSON.stringify(store));
}

function applyMap(map: SettingsMap): void {
  for (const [ns, entries] of Object.entries(map)) {
    if (!store[ns]) store[ns] = {};
    for (const [k, v] of Object.entries(entries)) {
      store[ns][k] = v;
    }
  }
}

// --- Public API ---

/** Read a single setting. Returns `fallback` when the key is absent. */
function get(namespace: string, key: string, fallback = ""): string {
  return store[namespace]?.[key] ?? fallback;
}

/** Return all key-value pairs in a namespace. */
function getNamespace(namespace: string): Record<string, string> {
  return store[namespace] ?? {};
}

/**
 * Write one or more keys in a namespace.
 * Updates local reactive store + localStorage cache immediately,
 * then persists to the backend asynchronously.
 */
function set(namespace: string, entries: Record<string, string>): void {
  if (!store[namespace]) store[namespace] = {};
  for (const [k, v] of Object.entries(entries)) {
    store[namespace][k] = v;
  }
  saveCache();
  putNamespace(namespace, entries).catch(() => {
    // Silently ignore network errors — cache is the source of truth for now
  });
}

/**
 * Hydrate the store: load localStorage cache first (sync),
 * then fetch from API and merge (async).
 * Safe to call multiple times — only the first call fetches.
 */
async function hydrate(): Promise<void> {
  if (hydrated) return;
  hydrated = true;

  // Instant: populate from cache
  applyMap(loadCache());

  // Background: sync from server
  try {
    const remote = await fetchAllSettings();
    applyMap(remote);
    saveCache();
  } catch {
    // Offline or backend unreachable — cache is enough
  }
}

export function useSettings() {
  return {
    store,
    get,
    getNamespace,
    set,
    hydrate,
    clearAll,
    exportAll,
    _reset,
  };
}

/**
 * Clear all settings: wipe reactive store, localStorage cache, and backend.
 */
async function clearAll(): Promise<void> {
  for (const key of Object.keys(store)) {
    delete store[key];
  }
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(CACHE_KEY);
  }
  await deleteAllSettings().catch(() => {});
}

/**
 * Export all settings as a JSON-serializable map.
 */
function exportAll(): SettingsMap {
  const snapshot: SettingsMap = {};
  for (const [ns, entries] of Object.entries(store)) {
    snapshot[ns] = { ...entries };
  }
  return snapshot;
}

/** Reset the store for test isolation. */
function _reset(): void {
  for (const key of Object.keys(store)) {
    delete store[key];
  }
  hydrated = false;
}
