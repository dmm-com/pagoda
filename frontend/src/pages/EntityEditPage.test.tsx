/**
 * @jest-environment jsdom
 */

import {
  EntityDetail,
  PaginatedEntityListList,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, render, screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";

import { editEntityPath } from "../routes/Routes";

import { EntityEditPage } from "./EntityEditPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { ACLType } from "services/ACLUtil";

const entityList: PaginatedEntityListList = {
  count: 3,
  results: [
    {
      id: 1,
      name: "aaa",
      note: "",
      isToplevel: false,
      permission: ACLType.Full,
    },
    {
      id: 2,
      name: "aaaaa",
      note: "",
      isToplevel: false,
      permission: ACLType.Full,
    },
    {
      id: 3,
      name: "bbbbb",
      note: "",
      isToplevel: false,
      permission: ACLType.Full,
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
  permission: ACLType.Full,
};

const server = setupServer(
  // getEntities
  http.get("http://localhost/entity/api/v2/", () => {
    return HttpResponse.json(entityList);
  }),
  // getEntity
  http.get("http://localhost/entity/api/v2/1/", () => {
    return HttpResponse.json(entity);
  }),
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
    const router = createMemoryRouter(
      [
        {
          path: editEntityPath(":entityId"),
          element: <EntityEditPage />,
        },
      ],
      {
        initialEntries: ["/ui/entities/1"],
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
});
