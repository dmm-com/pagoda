/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { JobListPage } from "pages/JobListPage";

const server = setupServer(
  // getRoles
  http.get("http://localhost/job/api/v2/jobs", () => {
    return HttpResponse.json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          operation: 1,
          status: 1,
          passed_time: 1,
          created_at: new Date("2022-01-01T09:00:00.000000+09:00"),
          text: "note",
          target: {
            id: 1,
            name: "target1",
            schema_id: null,
            schema_name: null,
          },
        },
        {
          id: 2,
          operation: 2,
          status: 2,
          passed_time: 2,
          created_at: new Date("2022-01-01T09:00:00.000000+09:00"),
          text: "note",
          target: {
            id: 2,
            name: "target2",
            schema_id: null,
            schema_name: null,
          },
        },
      ],
    });
  }),
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("JobListPage", () => {
  test("should match snapshot", async () => {
    const result = render(<JobListPage />, {
      wrapper: TestWrapper,
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(result).toMatchSnapshot();
  });
});
