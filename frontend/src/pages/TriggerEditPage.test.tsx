/**
 * @jest-environment jsdom
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { editTriggerPath } from "../routes/Routes";

import { TriggerEditPage } from "./TriggerEditPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";

const server = setupServer(
  // getTrigger
  http.get("http://localhost/trigger/api/v2/1", () => {
    return HttpResponse.json({
      id: 1,
      entity: {
        id: 1,
        name: "test entity",
        note: "",
        isToplevel: false,
        attrs: [],
        webhooks: [],
      },
      actions: [],
      conditions: [],
    });
  }),
  // getEntities
  http.get("http://localhost/entity/api/v2/", () => {
    return HttpResponse.json({
      count: 3,
      results: [
        {
          id: 1,
          name: "aaa",
          note: "",
          isToplevel: false,
          attrs: [],
          webhooks: [],
        },
        {
          id: 2,
          name: "aaaaa",
          note: "",
          isToplevel: false,
          attrs: [],
          webhooks: [],
        },
        {
          id: 3,
          name: "bbbbb",
          note: "",
          isToplevel: false,
          attrs: [],
          webhooks: [],
        },
      ],
    });
  }),
  // getEntity
  http.get("http://localhost/entity/api/v2/1/", () => {
    return HttpResponse.json({
      id: 1,
      name: "test entity",
      note: "",
      isToplevel: false,
      attrs: [],
      webhooks: [],
    });
  })
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("EditTriggerPage", () => {
  test("should match snapshot", async () => {
    const router = createMemoryRouter(
      [
        {
          path: editTriggerPath(":triggerId"),
          element: <TriggerEditPage />,
        },
      ],
      {
        initialEntries: ["/ui/triggers/1"],
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
