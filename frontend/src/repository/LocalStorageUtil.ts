export const LocalStorageKey = {
  JobLatestCheckDate: "job__latest_check_date",
} as const;

type LocalStorageKey = (typeof LocalStorageKey)[keyof typeof LocalStorageKey];

// A local storage wrapper to enforce callers specifying predefined key
class LocalStorageUtil {
  get(key: LocalStorageKey): string | null {
    return localStorage.getItem(key);
  }

  set(key: LocalStorageKey, value: string) {
    return localStorage.setItem(key, value);
  }
}

export const localStorageUtil = new LocalStorageUtil();
