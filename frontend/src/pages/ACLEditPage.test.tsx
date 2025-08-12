/**
 * @jest-environment jsdom
 */

import { render, screen, act, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { ACLEditPage } from "pages/ACLEditPage";
import { aclPath } from "routes/Routes";

const server = setupServer(
  // getAcl
  http.get("http://localhost/acl/api/v2/acls/1", () => {
    return HttpResponse.json({
      name: "acl1",
      objtype: 1,
      is_public: false,
      default_permission: 1,
      parent: {
        id: 10,
        name: "Entity1",
      },
      roles: [
        {
          id: 1,
          name: "member1",
          description: "",
          current_permission: 1,
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
      hasOngoingChanges: false,
      attrs: [],
      webhooks: [],
    });
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test("should match snapshot", async () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        is_superuser: false,
      },
    },
    writable: false,
  });

  const router = createMemoryRouter(
    [
      {
        path: aclPath(":objectId"),
        element: <ACLEditPage />,
      },
    ],
    {
      initialEntries: [aclPath(1)],
    },
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
