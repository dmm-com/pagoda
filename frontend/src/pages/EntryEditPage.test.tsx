/**
 */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";
import { useSWRConfig } from "swr";

import { EntryDetailsPage } from "./EntryDetailsPage";
import { EntryEditPage } from "./EntryEditPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import i18n from "i18n/config";
import { aironeApiClient } from "repository/AironeApiClient";
import { entryDetailsPath, entryEditPath, newEntryPath } from "routes/Routes";

const mockEntity = {
  id: 2,
  name: "test entity",
  note: "",
  item_name_type: "US",
  is_toplevel: false,
  attrs: [
    {
      id: 1,
      index: 0,
      name: "attr1",
      type: 2, // string
      is_mandatory: false,
      is_delete_in_chain: false,
      is_summarized: false,
      is_writable: true,
      referral: [],
      note: "",
      default_value: null,
      name_order: 0,
      name_prefix: "",
      name_postfix: "",
    },
  ],
  webhooks: [],
  isolation_rules: [],
  delete_chain_exclude_entities: [],
  is_public: false,
  has_ongoing_changes: false,
  permission: 3,
};

const mockEntry = {
  id: 1,
  name: "test entry",
  isActive: true,
  schema: {
    id: 2,
    name: "test entity",
  },
  attrs: [
    {
      id: 1,
      name: "attr1",
      type: 2,
      isMandatory: false,
      isWritable: true,
      value: { asString: "test value" },
      schema: { id: 1 },
    },
  ],
};

const server = setupServer(
  // getEntity
  http.get("http://localhost/entity/api/v2/2/", () => {
    return HttpResponse.json(mockEntity);
  }),
  // getEntry
  http.get("http://localhost/entry/api/v2/1/", () => {
    return HttpResponse.json(mockEntry);
  }),
  // getReferral (for attribute value fields)
  http.get("http://localhost/entry/api/v2/1/referral/", () => {
    return HttpResponse.json({
      count: 0,
      results: [],
    });
  }),
);

const RefreshEntry = () => {
  const { mutate } = useSWRConfig();
  return (
    <button
      onClick={() =>
        mutate(["entry", 1], aironeApiClient.getEntry(1), {
          revalidate: false,
        })
      }
    >
      再取得
    </button>
  );
};

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("EntryEditPage", () => {
  beforeEach(() => {
    Object.defineProperty(window, "django_context", {
      value: {
        user: {
          id: 1,
          username: "user1",
          isSuperuser: false,
          isReadonly: false,
          parentUser: null,
          email: "user1@example.com",
        },
      },
      writable: true,
      configurable: true,
    });
  });

  const renderEditPage = async (
    path: string = "/ui/entities/2/entries/1/edit",
  ) => {
    const router = createMemoryRouter(
      [
        {
          path: entryEditPath(":entityId", ":entryId"),
          element: <EntryEditPage />,
        },
        {
          path: newEntryPath(":entityId"),
          element: <EntryEditPage />,
        },
        {
          path: entryDetailsPath(":entityId", ":entryId"),
          element: <EntryDetailsPage />,
        },
      ],
      {
        initialEntries: [path],
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
  };

  test("should match snapshot", async () => {
    const router = createMemoryRouter(
      [
        {
          path: entryEditPath(":entityId", ":entryId"),
          element: <EntryEditPage />,
        },
      ],
      {
        initialEntries: ["/ui/entities/2/entries/1/edit"],
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

  test("keeps local edits when a background refresh brings newer entry data", async () => {
    let serverName = "test entry";
    server.use(
      http.get("http://localhost/entry/api/v2/1/", () =>
        HttpResponse.json({ ...mockEntry, name: serverName }),
      ),
    );
    const router = createMemoryRouter(
      [
        {
          path: entryEditPath(":entityId", ":entryId"),
          element: (
            <>
              <EntryEditPage />
              <RefreshEntry />
            </>
          ),
        },
      ],
      { initialEntries: ["/ui/entities/2/entries/1/edit"] },
    );
    render(<RouterProvider router={router} />, {
      wrapper: TestWrapperWithoutRoutes,
    });

    const name = await screen.findByRole("textbox", { name: "アイテム名" });
    await waitFor(() => expect(name).toHaveValue("test entry"));
    fireEvent.change(name, { target: { value: "local draft" } });
    serverName = "new server name";
    fireEvent.click(screen.getByRole("button", { name: "再取得" }));

    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: "new server name" }),
      ).toBeVisible(),
    );
    expect(name).toHaveValue("local draft");
  });

  describe("array attributes", () => {
    const arrayAttrs = [
      { id: 11, name: "arrStr", type: 1026 }, // array_string
      { id: 12, name: "arrNum", type: 1280 }, // array_number
      { id: 13, name: "arrNamed", type: 3073 }, // array_named_object
    ];
    const arrayEntity = {
      ...mockEntity,
      attrs: arrayAttrs.map((attr, index) => ({
        ...mockEntity.attrs[0],
        ...attr,
        index,
      })),
    };
    // The API returns snake_case JSON; the generated client maps it.
    const arrayEntry = (name: string, strings: string[]) => ({
      ...mockEntry,
      name,
      attrs: [
        { value: { as_array_string: strings } },
        { value: { as_array_number: [42] } },
        {
          value: {
            as_array_named_object: [{ name: "named-key", object: null }],
          },
        },
      ].map((attr, index) => ({
        ...arrayAttrs[index],
        ...attr,
        is_mandatory: false,
        is_writable: true,
        schema: { id: arrayAttrs[index].id, name: arrayAttrs[index].name },
      })),
    });

    const listItems = (attrName: string) => {
      const row = document.getElementById(`attrs-${attrName}`)?.closest("tr");
      expect(row).not.toBeNull();
      return within(row as HTMLElement).getAllByRole("listitem");
    };
    const rowValues = (attrName: string) =>
      listItems(attrName).flatMap((item) =>
        Array.from(item.querySelectorAll("input")).map((input) => input.value),
      );

    test("loads the item name and array values on first render", async () => {
      // Regression: array fields inserted placeholder rows during render,
      // which marked the form dirty before the loaded entry was applied, so
      // the item name and array values stayed empty.
      server.use(
        http.get("http://localhost/entity/api/v2/2/", () =>
          HttpResponse.json(arrayEntity),
        ),
        http.get("http://localhost/entry/api/v2/1/", () =>
          HttpResponse.json(arrayEntry("array entry", ["a", "b"])),
        ),
      );
      await renderEditPage();

      const name = await screen.findByRole("textbox", { name: "アイテム名" });
      await waitFor(() => expect(name).toHaveValue("array entry"));
      // Exactly the stored rows: no placeholder row may be added on top.
      expect(rowValues("arrStr")).toEqual(["a", "b"]);
      expect(rowValues("arrNum")).toEqual(["42"]);
      expect(rowValues("arrNamed")).toContain("named-key");
      expect(listItems("arrNamed")).toHaveLength(1);
      expect(screen.getByRole("button", { name: "保存" })).toBeDisabled();
    });

    test("keeps local array edits and applies untouched server changes on refresh", async () => {
      let current = arrayEntry("array entry", ["a", "b"]);
      server.use(
        http.get("http://localhost/entity/api/v2/2/", () =>
          HttpResponse.json(arrayEntity),
        ),
        http.get("http://localhost/entry/api/v2/1/", () =>
          HttpResponse.json(current),
        ),
      );
      const router = createMemoryRouter(
        [
          {
            path: entryEditPath(":entityId", ":entryId"),
            element: (
              <>
                <EntryEditPage />
                <RefreshEntry />
              </>
            ),
          },
        ],
        { initialEntries: ["/ui/entities/2/entries/1/edit"] },
      );
      render(<RouterProvider router={router} />, {
        wrapper: TestWrapperWithoutRoutes,
      });

      const name = await screen.findByRole("textbox", { name: "アイテム名" });
      await waitFor(() => expect(name).toHaveValue("array entry"));
      fireEvent.change(screen.getByDisplayValue("a"), {
        target: { value: "local a" },
      });

      current = arrayEntry("renamed on server", ["server a", "server b"]);
      fireEvent.click(screen.getByRole("button", { name: "再取得" }));

      await waitFor(() => expect(name).toHaveValue("renamed on server"));
      // Only the edited element is kept; untouched ones follow the server.
      expect(rowValues("arrStr")).toEqual(["local a", "server b"]);
      expect(rowValues("arrNum")).toEqual(["42"]);
    });

    test("starts a new item with an empty name and one empty row per array", async () => {
      server.use(
        http.get("http://localhost/entity/api/v2/2/", () =>
          HttpResponse.json(arrayEntity),
        ),
      );
      await renderEditPage("/ui/entities/2/entries/new");

      const name = await screen.findByRole("textbox", { name: "アイテム名" });
      expect(name).toHaveValue("");
      for (const attr of ["arrStr", "arrNum", "arrNamed"]) {
        expect(listItems(attr)).toHaveLength(1);
      }
    });
  });

  describe("rendering (edit mode)", () => {
    test("should render page header with entry name", async () => {
      await renderEditPage();

      // Entry name appears multiple times (header, breadcrumb, form)
      const entryNames = screen.getAllByText("test entry");
      expect(entryNames.length).toBeGreaterThan(0);
    });

    test("should render breadcrumbs", async () => {
      await renderEditPage();

      // Should show entity name in breadcrumbs
      expect(screen.getByText("test entity")).toBeInTheDocument();
    });

    test("should render save button", async () => {
      await renderEditPage();

      expect(screen.getByRole("button", { name: /保存/i })).toBeInTheDocument();
    });

    test("should render cancel button", async () => {
      await renderEditPage();

      expect(
        screen.getByRole("button", { name: /キャンセル/i }),
      ).toBeInTheDocument();
    });

    test("should render edit description", async () => {
      await renderEditPage();

      expect(screen.getByText("アイテム編集")).toBeInTheDocument();
    });
  });

  describe("rendering (create mode)", () => {
    test("should render new item title for create mode", async () => {
      await renderEditPage("/ui/entities/2/entries/new");

      await waitFor(() => {
        expect(screen.getByText("新規アイテムの作成")).toBeInTheDocument();
      });
    });
  });

  describe("loading state", () => {
    test("should show loading indicator initially", async () => {
      // Delay the API response to see loading state
      server.use(
        http.get("http://localhost/entity/api/v2/2/", async () => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          return HttpResponse.json(mockEntity);
        }),
      );

      const router = createMemoryRouter(
        [
          {
            path: entryEditPath(":entityId", ":entryId"),
            element: <EntryEditPage />,
          },
        ],
        {
          initialEntries: ["/ui/entities/2/entries/1/edit"],
        },
      );

      await act(async () => {
        render(<RouterProvider router={router} />, {
          wrapper: TestWrapperWithoutRoutes,
        });
      });

      // Loading should be shown initially
      expect(screen.getByTestId("loading")).toBeInTheDocument();
    });
  });

  describe("form elements", () => {
    test("should have name input field", async () => {
      await renderEditPage();

      // The form should have a name input (search by placeholder or role)
      const nameInputs = screen.getAllByRole("textbox");
      expect(nameInputs.length).toBeGreaterThan(0);
    });

    test("should display entry name in the form", async () => {
      await renderEditPage();

      // Entry name should be displayed somewhere in the form
      expect(screen.getByDisplayValue("test entry")).toBeInTheDocument();
    });
  });

  describe("button states", () => {
    test("save button should be disabled initially (form not dirty)", async () => {
      await renderEditPage();

      const saveButton = screen.getByRole("button", { name: /保存/i });
      expect(saveButton).toBeDisabled();
    });

    test("cancel button should be clickable", async () => {
      await renderEditPage();

      const cancelButton = screen.getByRole("button", { name: /キャンセル/i });
      expect(cancelButton).not.toBeDisabled();

      // Should not throw when clicked
      fireEvent.click(cancelButton);
    });
  });

  describe("form interaction", () => {
    test("should allow modifying entry name", async () => {
      await renderEditPage();

      const nameInput = screen.getByDisplayValue("test entry");
      fireEvent.change(nameInput, { target: { value: "modified entry" } });

      expect(screen.getByDisplayValue("modified entry")).toBeInTheDocument();
    });
  });

  describe("english rendering", () => {
    test("should render edit description and save/cancel buttons in english", async () => {
      await act(async () => {
        await i18n.changeLanguage("en");
      });

      await renderEditPage();

      expect(screen.getByText("Edit entry")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Save/i })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Cancel/i }),
      ).toBeInTheDocument();
    });

    test("should render new entry title in english for create mode", async () => {
      await act(async () => {
        await i18n.changeLanguage("en");
      });

      await renderEditPage("/ui/entities/2/entries/new");

      await waitFor(() => {
        expect(screen.getByText("Create a new entry")).toBeInTheDocument();
      });
    });
  });
});
