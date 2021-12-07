/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import React from "react";
import { MemoryRouter } from "react-router-dom";

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
  const { container } = render(<Entity />, {
    wrapper: MemoryRouter,
  });
  await waitForElementToBeRemoved(screen.getByTestId("loading"));

  /**
   * NOTE It's a workaround for Material-UI v4 issue on snapshot testing. It works but make snapshot HTML not-human-readable.
   * see also https://github.com/mui-org/material-ui/issues/21293#issuecomment-654921524
   */
  const modifiedHtml = container.innerHTML
    .replace(/id="mui-[0-9]*"/g, "")
    .replace(/aria-labelledby="(mui-[0-9]* *)*"/g, "");

  expect(modifiedHtml).toMatchSnapshot();
});
