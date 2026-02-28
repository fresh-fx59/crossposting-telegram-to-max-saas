export function getStoredValue(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function setStoredValue(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Ignore storage write failures (privacy mode / blocked storage).
  }
}

export function removeStoredValue(key: string): void {
  try {
    window.localStorage.removeItem(key);
  } catch {
    // Ignore storage removal failures.
  }
}
