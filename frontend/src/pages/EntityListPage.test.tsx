/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { EntityListPage } from "pages/EntityListPage";

const server = setupServer(
  // getEntities
  http.get("http://localhost/entity/api/v2/", () => {
    return HttpResponse.json({
      count: 3,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          name: "aaa",
          note: "",
          is_toplevel: false,
          attrs: [],
        },
        {
          id: 2,
          name: "aaaaa",
          note: "",
          is_toplevel: false,
          attrs: [],
        },
        {
          id: 3,
          name: "bbbbb",
          note: "",
          is_toplevel: false,
          attrs: [],
        },
      ],
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("EntityListPage", () => {
  test("should match snapshot", async () => {
    const result = render(<EntityListPage />, {
      wrapper: TestWrapper,
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(result).toMatchSnapshot();
  });
});
