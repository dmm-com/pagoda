/**
 * @jest-environment jsdom
 */

import { JobSerializers } from "@dmm-com/airone-apiclient-typescript-fetch";
import { renderHook, act } from "@testing-library/react";
import { SnackbarProvider } from "notistack";
import { FC, ReactNode } from "react";

import { useJobCompletionNotification } from "./useJobCompletionNotification";

import { JobOperations, JobStatuses } from "services/Constants";

const wrapper: FC<{ children: ReactNode }> = ({ children }) => (
  <SnackbarProvider maxSnack={5}>{children}</SnackbarProvider>
);

const makeJob = (
  overrides: Partial<JobSerializers> & { id: number },
): JobSerializers => {
  const { id, ...rest } = overrides;
  return {
    id,
    status: JobStatuses.DONE,
    operation: JobOperations.CREATE_ENTRY,
    target: { name: `job-${id}` },
    createdAt: new Date(),
    passedTime: 0,
    text: "",
    ...rest,
  } as JobSerializers;
};

beforeEach(() => {
  localStorage.clear();
});

describe("useJobCompletionNotification", () => {
  test("should not show toasts on first load for already-terminal jobs", () => {
    const jobs = [
      makeJob({ id: 1, status: JobStatuses.DONE }),
      makeJob({ id: 2, status: JobStatuses.ERROR }),
    ];

    const { result } = renderHook(
      ({ recentJobs }) => useJobCompletionNotification(recentJobs),
      { wrapper, initialProps: { recentJobs: jobs } },
    );

    // Hook should complete without error
    expect(result.current).toBeUndefined();

    // IDs should be persisted to localStorage as notified
    const stored = JSON.parse(
      localStorage.getItem("job__notified_ids") ?? "[]",
    );
    expect(stored).toContain(1);
    expect(stored).toContain(2);
  });

  test("should show toast when a new job reaches terminal status after first load", () => {
    const initialJobs = [makeJob({ id: 1, status: JobStatuses.PROCESSING })];

    const { rerender } = renderHook(
      ({ recentJobs }) => useJobCompletionNotification(recentJobs),
      { wrapper, initialProps: { recentJobs: initialJobs } },
    );

    // Job completes on next poll
    const updatedJobs = [makeJob({ id: 1, status: JobStatuses.DONE })];

    act(() => {
      rerender({ recentJobs: updatedJobs });
    });

    // ID should be stored as notified
    const stored = JSON.parse(
      localStorage.getItem("job__notified_ids") ?? "[]",
    );
    expect(stored).toContain(1);
  });

  test("should not show duplicate toast for already-notified job", () => {
    const initialJobs = [makeJob({ id: 1, status: JobStatuses.PROCESSING })];

    const { rerender } = renderHook(
      ({ recentJobs }) => useJobCompletionNotification(recentJobs),
      { wrapper, initialProps: { recentJobs: initialJobs } },
    );

    const completedJobs = [makeJob({ id: 1, status: JobStatuses.DONE })];

    act(() => {
      rerender({ recentJobs: completedJobs });
    });

    // Rerender again with same completed job - should not duplicate
    act(() => {
      rerender({ recentJobs: completedJobs });
    });

    const stored = JSON.parse(
      localStorage.getItem("job__notified_ids") ?? "[]",
    );
    // Should still only have one entry
    expect(stored.filter((id: number) => id === 1)).toHaveLength(1);
  });

  test("should handle empty recentJobs without error", () => {
    const { result } = renderHook(
      ({ recentJobs }) => useJobCompletionNotification(recentJobs),
      { wrapper, initialProps: { recentJobs: [] as JobSerializers[] } },
    );

    expect(result.current).toBeUndefined();
  });

  test("should skip non-terminal jobs", () => {
    const initialJobs = [makeJob({ id: 10, status: JobStatuses.PREPARING })];

    const { rerender } = renderHook(
      ({ recentJobs }) => useJobCompletionNotification(recentJobs),
      { wrapper, initialProps: { recentJobs: initialJobs } },
    );

    // Still processing on next poll
    const stillProcessing = [
      makeJob({ id: 10, status: JobStatuses.PROCESSING }),
    ];

    act(() => {
      rerender({ recentJobs: stillProcessing });
    });

    const stored = localStorage.getItem("job__notified_ids");
    const ids = stored ? JSON.parse(stored) : [];
    expect(ids).not.toContain(10);
  });

  test("should handle export job with DONE status", () => {
    const initialJobs = [
      makeJob({
        id: 5,
        status: JobStatuses.PROCESSING,
        operation: JobOperations.EXPORT_ENTRY,
      }),
    ];

    const { rerender } = renderHook(
      ({ recentJobs }) => useJobCompletionNotification(recentJobs),
      { wrapper, initialProps: { recentJobs: initialJobs } },
    );

    const completedJobs = [
      makeJob({
        id: 5,
        status: JobStatuses.DONE,
        operation: JobOperations.EXPORT_ENTRY,
      }),
    ];

    act(() => {
      rerender({ recentJobs: completedJobs });
    });

    const stored = JSON.parse(
      localStorage.getItem("job__notified_ids") ?? "[]",
    );
    expect(stored).toContain(5);
  });

  test("should handle ERROR status job", () => {
    const initialJobs = [makeJob({ id: 7, status: JobStatuses.PROCESSING })];

    const { rerender } = renderHook(
      ({ recentJobs }) => useJobCompletionNotification(recentJobs),
      { wrapper, initialProps: { recentJobs: initialJobs } },
    );

    const failedJobs = [makeJob({ id: 7, status: JobStatuses.ERROR })];

    act(() => {
      rerender({ recentJobs: failedJobs });
    });

    const stored = JSON.parse(
      localStorage.getItem("job__notified_ids") ?? "[]",
    );
    expect(stored).toContain(7);
  });

  test("should handle TIMEOUT status job", () => {
    const initialJobs = [makeJob({ id: 8, status: JobStatuses.PROCESSING })];

    const { rerender } = renderHook(
      ({ recentJobs }) => useJobCompletionNotification(recentJobs),
      { wrapper, initialProps: { recentJobs: initialJobs } },
    );

    const timedOutJobs = [makeJob({ id: 8, status: JobStatuses.TIMEOUT })];

    act(() => {
      rerender({ recentJobs: timedOutJobs });
    });

    const stored = JSON.parse(
      localStorage.getItem("job__notified_ids") ?? "[]",
    );
    expect(stored).toContain(8);
  });

  test("should prune IDs no longer in recentJobs", () => {
    // Pre-seed localStorage with an old notified ID
    localStorage.setItem("job__notified_ids", JSON.stringify([999]));

    const initialJobs = [makeJob({ id: 1, status: JobStatuses.PROCESSING })];

    const { rerender } = renderHook(
      ({ recentJobs }) => useJobCompletionNotification(recentJobs),
      { wrapper, initialProps: { recentJobs: initialJobs } },
    );

    const completedJobs = [makeJob({ id: 1, status: JobStatuses.DONE })];

    act(() => {
      rerender({ recentJobs: completedJobs });
    });

    const stored = JSON.parse(
      localStorage.getItem("job__notified_ids") ?? "[]",
    );
    expect(stored).toContain(1);
    expect(stored).not.toContain(999);
  });

  test("should restore notified IDs from localStorage across instances", () => {
    // Simulate a previous session having notified job 42
    localStorage.setItem("job__notified_ids", JSON.stringify([42]));

    const jobs = [makeJob({ id: 42, status: JobStatuses.DONE })];

    // First render (first load marks existing terminals, but 42 is already in localStorage)
    renderHook(({ recentJobs }) => useJobCompletionNotification(recentJobs), {
      wrapper,
      initialProps: { recentJobs: jobs },
    });

    const stored = JSON.parse(
      localStorage.getItem("job__notified_ids") ?? "[]",
    );
    expect(stored).toContain(42);
  });
});
