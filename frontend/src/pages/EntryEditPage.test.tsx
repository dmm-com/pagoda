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
import { MemoryRouter, Route } from "react-router-dom";

import { EntryEditPage } from "./EntryEditPage";

import { entryEditPath } from "Routes";
import { TestWrapper } from "TestWrapper";

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
    // wait async calls and get rendered fragment
    const result = render(
      <MemoryRouter initialEntries={["/ui/entities/2/entries/1/edit"]}>
        <Route
          path={entryEditPath(":entityId", ":entryId")}
          element={<EntryEditPage />}
        />
      </MemoryRouter>,
      {
        wrapper: TestWrapper,
      }
    );
    await waitForElementToBeRemoved(screen.getByTestId("loading"));

    expect(result).toMatchSnapshot();
  });
});
