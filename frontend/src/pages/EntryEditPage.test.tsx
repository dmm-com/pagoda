/**
 * @jest-environment jsdom
 */

import { render, screen, act, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { EntryEditPage } from "./EntryEditPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { entryEditPath } from "routes/Routes";

const server = setupServer(
  // getEntity
  http.get("http://localhost/entity/api/v2/2/", () => {
    return HttpResponse.json({
      id: 2,
      name: "test entity",
      note: "",
      isToplevel: false,
      attrs: [],
      webhooks: [],
    });
  }),
  // getEntry
  http.get("http://localhost/entry/api/v2/1/", () => {
    return HttpResponse.json({
      id: 1,
      name: "test entry",
      isActive: true,
      schema: {
        id: 2,
        name: "test entity",
      },
      attrs: [],
    });
  })
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("EntryEditPage", () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        is_superuser: false,
      },
    },
    writable: false,
  });

  test("should match snapshot", async () => {
    const router = createMemoryRouter(
      [
        {
          path: entryEditPath(":entityId", ":entryId"),
          element: <EntryEditPage />,
        },
      ],
      {
        initialEntries: ["/ui/entities/2/entries/1/edit"],
      }
    );
    const result = await act(async () => {
      return render(<RouterProvider router={router} />, {
        wrapper: TestWrapperWithoutRoutes,
      });
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(result).toMatchSnapshot();
  });
});
