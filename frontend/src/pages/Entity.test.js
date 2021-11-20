/**
 * @jest-environment jsdom
 */

import { render, waitFor } from "@testing-library/react";
import React from "react";
import { MemoryRouter } from "react-router-dom";

import { Entity } from "./Entity";

afterEach(() => {
  jest.clearAllMocks();
});

test("should match snapshot", async () => {
  const entities = [
    {
      id: "1",
      name: "aaa",
      note: "",
    },
    {
      id: "2",
      name: "aaaaa",
      note: "",
    },
    {
      id: "3",
      name: "bbbbb",
      note: "",
    },
  ];

  /* eslint-disable */
  jest
    .spyOn(require("../utils/AironeAPIClient"), "getEntities")
    .mockResolvedValueOnce({
      json() {
        return Promise.resolve({
          entities: entities,
        });
      },
    });
  /* eslint-enable */

  const fragment = await waitFor(() => {
    return render(<Entity />, {
      wrapper: MemoryRouter,
    }).asFragment();
  });

  expect(fragment).toMatchSnapshot();
});
