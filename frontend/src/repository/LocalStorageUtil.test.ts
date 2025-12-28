/**
 * @jest-environment jsdom
 */

import { LocalStorageKey, localStorageUtil } from "./LocalStorageUtil";

describe("LocalStorageUtil", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe("get", () => {
    test("should return null when key does not exist", () => {
      const result = localStorageUtil.get(LocalStorageKey.JobLatestCheckDate);

      expect(result).toBeNull();
    });

    test("should return stored value when key exists", () => {
      const testValue = "2024-01-01T00:00:00.000Z";
      localStorage.setItem(LocalStorageKey.JobLatestCheckDate, testValue);

      const result = localStorageUtil.get(LocalStorageKey.JobLatestCheckDate);

      expect(result).toBe(testValue);
    });

    test("should return correct value for specific key", () => {
      const testValue = "test-value";
      localStorage.setItem(LocalStorageKey.JobLatestCheckDate, testValue);

      const result = localStorageUtil.get(LocalStorageKey.JobLatestCheckDate);

      expect(result).toBe(testValue);
    });
  });

  describe("set", () => {
    test("should store value in localStorage", () => {
      const testValue = "2024-01-01T00:00:00.000Z";

      localStorageUtil.set(LocalStorageKey.JobLatestCheckDate, testValue);

      expect(localStorage.getItem(LocalStorageKey.JobLatestCheckDate)).toBe(
        testValue,
      );
    });

    test("should overwrite existing value", () => {
      const initialValue = "initial-value";
      const newValue = "new-value";

      localStorageUtil.set(LocalStorageKey.JobLatestCheckDate, initialValue);
      localStorageUtil.set(LocalStorageKey.JobLatestCheckDate, newValue);

      expect(localStorage.getItem(LocalStorageKey.JobLatestCheckDate)).toBe(
        newValue,
      );
    });

    test("should store empty string", () => {
      localStorageUtil.set(LocalStorageKey.JobLatestCheckDate, "");

      expect(localStorage.getItem(LocalStorageKey.JobLatestCheckDate)).toBe("");
    });
  });

  describe("LocalStorageKey", () => {
    test("should have correct key value for JobLatestCheckDate", () => {
      expect(LocalStorageKey.JobLatestCheckDate).toBe("job__latest_check_date");
    });
  });
});
