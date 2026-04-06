export type SettingsMap = Record<string, Record<string, string>>;

export async function fetchAllSettings(): Promise<SettingsMap> {
  const response = await fetch("/api/settings", {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error("Failed to fetch settings.");
  return (await response.json()) as SettingsMap;
}

export async function fetchNamespace(
  namespace: string,
): Promise<Record<string, string>> {
  const response = await fetch(
    `/api/settings/${encodeURIComponent(namespace)}`,
    {
      headers: { Accept: "application/json" },
    },
  );
  if (!response.ok) throw new Error(`Failed to fetch settings/${namespace}.`);
  return (await response.json()) as Record<string, string>;
}

export async function putSetting(
  namespace: string,
  key: string,
  value: string,
): Promise<void> {
  const response = await fetch(
    `/api/settings/${encodeURIComponent(namespace)}/${encodeURIComponent(key)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    },
  );
  if (!response.ok)
    throw new Error(`Failed to save setting ${namespace}/${key}.`);
}

export async function putNamespace(
  namespace: string,
  settings: Record<string, string>,
): Promise<void> {
  const response = await fetch(
    `/api/settings/${encodeURIComponent(namespace)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    },
  );
  if (!response.ok) throw new Error(`Failed to save settings/${namespace}.`);
}

export async function deleteAllSettings(): Promise<number> {
  const response = await fetch("/api/settings", { method: "DELETE" });
  if (!response.ok) throw new Error("Failed to clear settings.");
  const data = (await response.json()) as { deleted: number };
  return data.deleted;
}

export interface ProviderConfig {
  endpoint: string;
  model: string;
  apiKey?: string;
}

export async function fetchProvider(): Promise<ProviderConfig> {
  const response = await fetch("/api/provider", {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    return { endpoint: "http://localhost:11434", model: "" };
  }
  return (await response.json()) as ProviderConfig;
}

export async function setProvider(config: ProviderConfig): Promise<void> {
  await fetch("/api/provider", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
}

export interface TestResult {
  ok: boolean;
  message: string;
}

export async function testProvider(): Promise<TestResult> {
  const response = await fetch("/api/provider/test", {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    return { ok: false, message: "Request failed" };
  }
  return (await response.json()) as TestResult;
}
