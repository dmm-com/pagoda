/**
 * @jest-environment jsdom
 */

import {
  EntityDetail,
  PaginatedEntityListList,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  render,
  screen,
  waitForElementToBeRemoved,
} from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { MemoryRouter, Route } from "react-router-dom";

import { editEntityPath } from "../Routes";

import { EntityEditPage } from "./EntityEditPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";

const entityList: PaginatedEntityListList = {
  count: 3,
  results: [
    {
      id: 1,
      name: "aaa",
      note: "",
      isToplevel: false,
    },
    {
      id: 2,
      name: "aaaaa",
      note: "",
      isToplevel: false,
    },
    {
      id: 3,
      name: "bbbbb",
      note: "",
      isToplevel: false,
    },
  ],
};

const entity: EntityDetail = {
  id: 1,
  name: "test entity",
  note: "",
  isToplevel: false,
  hasOngoingChanges: false,
  attrs: [],
  webhooks: [],
};

const server = setupServer(
  // getEntities
  http.get("http://localhost/entity/api/v2/", () => {
    return HttpResponse.json(entityList);
  }),
  // getEntity
  http.get("http://localhost/entity/api/v2/1/", () => {
    return HttpResponse.json(entity);
  })
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("EditEntityPage", () => {
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
      <MemoryRouter initialEntries={["/ui/entities/1"]}>
        <Route
          path={editEntityPath(":entityId")}
          element={<EntityEditPage />}
        />
      </MemoryRouter>,
      {
        wrapper: TestWrapperWithoutRoutes,
      }
    );
    await waitForElementToBeRemoved(screen.getByTestId("loading"));

    expect(result).toMatchSnapshot();
  });
});
