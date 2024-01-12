/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";
import { MemoryRouter, Route } from "react-router-dom";

import { EntryEditPage } from "./EntryEditPage";

import { entryEditPath } from "Routes";
import { TestWrapper } from "TestWrapper";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        is_superuser: false,
      },
    },
    writable: false,
  });

  const entity = {
    id: 2,
    name: "bbb",
    note: "",
    isToplevel: false,
    attrs: [],
  };

  const entry = {
    id: 1,
    name: "aaa",
    isActive: true,
    schema: {
      id: 2,
      name: "bbb",
    },
    attrs: [],
  };

  /* eslint-disable */
  jest
    .spyOn(
      require("../repository/AironeApiClient").aironeApiClient,
      "getEntity"
    )
    .mockResolvedValue(Promise.resolve(entity));

  jest
    .spyOn(require("repository/AironeApiClient").aironeApiClient, "getEntry")
    .mockResolvedValue(Promise.resolve(entry));
  /* eslint-enable */

  // wait async calls and get rendered fragment
  const result = render(
    <MemoryRouter initialEntries={["/ui/entities/2/entries/1/edit"]}>
      <Route
        path={entryEditPath(":entityId", ":entryId")}
        component={EntryEditPage}
      />
    </MemoryRouter>,
    {
      wrapper: TestWrapper,
    }
  );
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
