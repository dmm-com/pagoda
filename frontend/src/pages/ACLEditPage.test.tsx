/**
 * @jest-environment jsdom
 */

import { render, screen, act, waitFor } from "@testing-library/react";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { ACLEditPage } from "pages/ACLEditPage";

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

  const acl = {
    name: "acl1",
    objtype: "type1",
    is_public: false,
    default_permission: 1,
    parent: {
      id: 10,
      name: "Entity1",
    },
    acltypes: [
      {
        id: 1,
        name: "type1",
      },
    ],
    roles: [
      {
        id: 1,
        name: "member1",
        type: 1,
        current_permission: 1,
      },
    ],
  };

  /* eslint-disable */
  jest
    .spyOn(require("../repository/AironeApiClient").aironeApiClient, "getAcl")
    .mockResolvedValue(Promise.resolve(acl));
  /* eslint-enable */

  const router = createMemoryRouter([
    {
      path: "/",
      element: <ACLEditPage />,
    },
  ]);
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
