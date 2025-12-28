/**
 * @jest-environment jsdom
 */

import { renderHook } from "@testing-library/react";

import { usePageTitle } from "./usePageTitle";

describe("usePageTitle", () => {
  const originalTitle = document.title;

  beforeEach(() => {
    document.title = "Original Title";
  });

  afterEach(() => {
    document.title = originalTitle;
  });

  test("should set document title when title is provided", () => {
    renderHook(() => usePageTitle("New Title"));

    expect(document.title).toBe("New Title");
  });

  test("should set document title with prefix when both title and prefix are provided", () => {
    renderHook(() => usePageTitle("Page Title", { prefix: "App" }));

    expect(document.title).toBe("App - Page Title");
  });

  test("should keep original title when title is undefined", () => {
    renderHook(() => usePageTitle(undefined));

    expect(document.title).toBe("Original Title");
  });

  test("should keep original title when title is empty string", () => {
    renderHook(() => usePageTitle(""));

    expect(document.title).toBe("Original Title");
  });

  test("should restore original title on unmount", () => {
    const { unmount } = renderHook(() => usePageTitle("Temporary Title"));

    expect(document.title).toBe("Temporary Title");

    unmount();

    expect(document.title).toBe("Original Title");
  });

  test("should update title when title prop changes", () => {
    const { rerender } = renderHook(({ title }) => usePageTitle(title), {
      initialProps: { title: "First Title" },
    });

    expect(document.title).toBe("First Title");

    rerender({ title: "Second Title" });

    expect(document.title).toBe("Second Title");
  });

  test("should update title when prefix changes", () => {
    const { rerender } = renderHook(
      ({ title, options }) => usePageTitle(title, options),
      { initialProps: { title: "Page", options: { prefix: "App1" } } },
    );

    expect(document.title).toBe("App1 - Page");

    rerender({ title: "Page", options: { prefix: "App2" } });

    expect(document.title).toBe("App2 - Page");
  });

  test("should handle prefix without title gracefully", () => {
    renderHook(() => usePageTitle(undefined, { prefix: "App" }));

    expect(document.title).toBe("Original Title");
  });
});
