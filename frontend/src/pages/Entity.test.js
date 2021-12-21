/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../utils/TestWrapper";

import { Entity } from "./Entity";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const entities = [
    {
      id: 1,
      name: "aaa",
      note: "",
    },
    {
      id: 2,
      name: "aaaaa",
      note: "",
    },
    {
      id: 3,
      name: "bbbbb",
      note: "",
    },
  ];

  jest
    .spyOn(require("../utils/AironeAPIClient"), "getEntities")
    .mockResolvedValue({
      json() {
        return Promise.resolve({
          entities: entities,
        });
      },
    });

  // wait async calls and get rendered fragment
  const result = render(<Entity />, {
    wrapper: TestWrapper,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  expect(result).toMatchSnapshot();
});
