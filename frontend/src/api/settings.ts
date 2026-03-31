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
