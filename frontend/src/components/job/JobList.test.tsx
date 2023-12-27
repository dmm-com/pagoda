/**
 * @jest-environment jsdom
 */

import { JobSerializers } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../TestWrapper";
import { JobOperations, JobStatuses } from "../../services/Constants";

import { JobList } from "./JobList";

describe("JobList", () => {
  test("should show appropriate links", async () => {
    const jobs = Object.values(JobOperations).map(
      (operation, index): JobSerializers => ({
        id: index,
        text: `operation-${index}`,
        status: JobStatuses.DONE,
        operation,
        target: {
          id: 1,
          name: "test",
          schemaId: null,
          schemaName: null,
        },
        createdAt: new Date(),
        passedTime: 0,
      }),
    );

    render(<JobList jobs={jobs} />, {
      wrapper: TestWrapper,
    });

    // 16 operations should have a link to their target, like to an entity
    // NOTE: Possible links on the screen are links to a target or download links
    expect(
      screen.queryAllByRole("link", {
        name: (content) => !content.includes("Download"),
      }),
    ).toHaveLength(16);

    // 4 export operations should have a download link
    expect(
      screen.queryAllByRole("link", {
        name: (content) => content.includes("Download"),
      }),
    ).toHaveLength(4);
  });

  test("should show operation buttons based on job status", async () => {
    const jobs = Object.values(JobStatuses).map(
      (status, index): JobSerializers => ({
        id: index,
        text: `status-${index}`,
        status,
        operation: JobOperations.CREATE_ENTRY,
        target: {
          id: 1,
          name: "test",
          schemaId: null,
          schemaName: null,
        },
        createdAt: new Date(),
        passedTime: 0,
      }),
    );

    render(<JobList jobs={jobs} />, {
      wrapper: TestWrapper,
    });

    // jobs with "PREPARING", "TIMEOUT", "ERROR" should have a retry button
    expect(screen.queryAllByRole("button", { name: "再実行" })).toHaveLength(3);

    // jobs with "PREPARING", "PROCESSING", "TIMEOUT" should have a cancel button
    expect(
      screen.queryAllByRole("button", { name: "キャンセル" }),
    ).toHaveLength(3);
  });
});
