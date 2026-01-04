/**
 * @jest-environment jsdom
 */

import {
  formatDateTime,
  formatDate,
  setJSTdate,
  DAY_OF_WEEK,
} from "./DateUtil";

describe("DateUtil", () => {
  describe("formatDateTime", () => {
    test("should format date with time correctly", () => {
      const date = new Date(2024, 0, 15, 14, 30, 45); // Jan 15, 2024, 14:30:45

      const result = formatDateTime(date);

      expect(result).toBe("2024/1/15 14:30:45");
    });

    test("should handle single digit month and day", () => {
      const date = new Date(2024, 0, 5, 9, 5, 3); // Jan 5, 2024, 09:05:03

      const result = formatDateTime(date);

      expect(result).toBe("2024/1/5 9:5:3");
    });

    test("should handle midnight", () => {
      const date = new Date(2024, 5, 20, 0, 0, 0); // Jun 20, 2024, 00:00:00

      const result = formatDateTime(date);

      expect(result).toBe("2024/6/20 0:0:0");
    });

    test("should handle end of day", () => {
      const date = new Date(2024, 11, 31, 23, 59, 59); // Dec 31, 2024, 23:59:59

      const result = formatDateTime(date);

      expect(result).toBe("2024/12/31 23:59:59");
    });
  });

  describe("formatDate", () => {
    test("should format date in Japanese locale with zero-padded values", () => {
      const date = new Date(2024, 0, 15); // Jan 15, 2024

      const result = formatDate(date);

      expect(result).toBe("2024/01/15");
    });

    test("should handle single digit month and day with zero padding", () => {
      const date = new Date(2024, 0, 5); // Jan 5, 2024

      const result = formatDate(date);

      expect(result).toBe("2024/01/05");
    });

    test("should handle December correctly", () => {
      const date = new Date(2024, 11, 25); // Dec 25, 2024

      const result = formatDate(date);

      expect(result).toBe("2024/12/25");
    });
  });

  describe("setJSTdate", () => {
    test("should set time to 9:00:00.000 (JST midnight in UTC)", () => {
      const date = new Date(2024, 0, 15, 14, 30, 45, 123);

      const result = setJSTdate(date);

      expect(result.getHours()).toBe(9);
      expect(result.getMinutes()).toBe(0);
      expect(result.getSeconds()).toBe(0);
      expect(result.getMilliseconds()).toBe(0);
    });

    test("should return the same date object (mutates in place)", () => {
      const date = new Date(2024, 0, 15, 14, 30, 45);

      const result = setJSTdate(date);

      expect(result).toBe(date);
    });

    test("should preserve year, month, and day", () => {
      const date = new Date(2024, 5, 20, 23, 59, 59);

      const result = setJSTdate(date);

      expect(result.getFullYear()).toBe(2024);
      expect(result.getMonth()).toBe(5); // June (0-indexed)
      expect(result.getDate()).toBe(20);
    });
  });

  describe("DAY_OF_WEEK", () => {
    test("should have Japanese day names in correct order", () => {
      expect(DAY_OF_WEEK.jp).toEqual([
        "日",
        "月",
        "火",
        "水",
        "木",
        "金",
        "土",
      ]);
    });

    test("should have 7 days", () => {
      expect(DAY_OF_WEEK.jp.length).toBe(7);
    });

    test("should start with Sunday (日)", () => {
      expect(DAY_OF_WEEK.jp[0]).toBe("日");
    });

    test("should end with Saturday (土)", () => {
      expect(DAY_OF_WEEK.jp[6]).toBe("土");
    });
  });
});
