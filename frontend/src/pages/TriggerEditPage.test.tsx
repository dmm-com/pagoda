/**
 * @jest-environment jsdom
 */

import { act, render } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { MemoryRouter, Route } from "react-router-dom";

import { editTriggerPath } from "../Routes";

import { TriggerEditPage } from "./TriggerEditPage";

import { TestWrapper } from "TestWrapper";

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
    const result = await act(async () => {
      return render(
        <MemoryRouter initialEntries={["/ui/triggers/1"]}>
          <Route
            path={editTriggerPath(":triggerId")}
            component={TriggerEditPage}
          />
        </MemoryRouter>,
        {
          wrapper: TestWrapper,
        }
      );
    });

    expect(result).toMatchSnapshot();
  });
});
