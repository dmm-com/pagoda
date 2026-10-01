/**
 */

import { PaginatedEntityListList } from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";

import { editEntityPath, newEntityPath } from "../routes/Routes";

import { EntityEditPage } from "./EntityEditPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import i18n from "i18n/config";
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

const entity = {
  id: 1,
  name: "test entity",
  note: "",
  isToplevel: false,
  hasOngoingChanges: false,
  attrs: [],
  webhooks: [],
  isolation_rules: [],
  delete_chain_exclude_entities: [],
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

  test("should render the new entity title in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });

    const router = createMemoryRouter(
      [
        {
          path: newEntityPath(),
          element: <EntityEditPage />,
        },
      ],
      {
        initialEntries: [newEntityPath()],
      },
    );
    await act(async () => {
      render(<RouterProvider router={router} />, {
        wrapper: TestWrapperWithoutRoutes,
      });
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(screen.getByText("Create a new entity")).toBeInTheDocument();
    expect(screen.getByText("Save")).toBeInTheDocument();
  });
});
