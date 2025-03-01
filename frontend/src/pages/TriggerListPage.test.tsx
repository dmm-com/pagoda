/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";

import { TriggerListPage } from "./TriggerListPage";

import { TestWrapper } from "TestWrapper";

const server = setupServer(
  // getTriggers
  http.get("http://localhost/trigger/api/v2/", () => {
    return HttpResponse.json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          entity: {
            id: 1,
            name: "test entity1",
            note: "",
            isToplevel: false,
            attrs: [],
            webhooks: [],
          },
          actions: [],
          conditions: [],
        },
        {
          id: 2,
          entity: {
            id: 2,
            name: "test entity2",
            note: "",
            isToplevel: false,
            attrs: [],
            webhooks: [],
          },
          actions: [],
          conditions: [],
        },
      ],
    });
  }),
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("TriggerPage", () => {
  test("should match snapshot", async () => {
    // wait async calls and get rendered fragment
    const result = render(<TriggerListPage />, {
      wrapper: TestWrapper,
    });
    await waitForElementToBeRemoved(screen.getByTestId("loading"));

    expect(result).toMatchSnapshot();
  });
});
