/**
 */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";

import { editTriggerPath } from "../routes/Routes";

import { TriggerEditPage } from "./TriggerEditPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import i18n from "i18n/config";

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
        isolation_rules: [],
        delete_chain_exclude_entities: [],
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
          isolation_rules: [],
          delete_chain_exclude_entities: [],
        },
        {
          id: 2,
          name: "aaaaa",
          note: "",
          isToplevel: false,
          attrs: [],
          webhooks: [],
          isolation_rules: [],
          delete_chain_exclude_entities: [],
        },
        {
          id: 3,
          name: "bbbbb",
          note: "",
          isToplevel: false,
          attrs: [],
          webhooks: [],
          isolation_rules: [],
          delete_chain_exclude_entities: [],
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
      isolation_rules: [],
      delete_chain_exclude_entities: [],
    });
  }),
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("EditTriggerPage", () => {
  test("should match snapshot", async () => {
    const router = createMemoryRouter(
      [
        {
          path: editTriggerPath(":triggerId"),
          element: <TriggerEditPage />,
        },
      ],
      {
        initialEntries: ["/ui/triggers/1"],
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

  test("filters model candidates regardless of width and case", async () => {
    const router = createMemoryRouter(
      [{ path: editTriggerPath(":triggerId"), element: <TriggerEditPage /> }],
      { initialEntries: ["/ui/triggers/1"] },
    );
    render(<RouterProvider router={router} />, {
      wrapper: TestWrapperWithoutRoutes,
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    fireEvent.change(screen.getAllByRole("combobox")[0], {
      target: { value: "ＡＡ" },
    });

    expect(await screen.findByText("aaaaa")).toBeInTheDocument();
  });

  test("renders in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });

    const router = createMemoryRouter(
      [
        {
          path: editTriggerPath(":triggerId"),
          element: <TriggerEditPage />,
        },
      ],
      {
        initialEntries: ["/ui/triggers/1"],
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

    expect(screen.getByText("Target model")).toBeInTheDocument();
    expect(screen.getByText("Conditions")).toBeInTheDocument();
    expect(screen.getByText("Actions")).toBeInTheDocument();
  });
});
