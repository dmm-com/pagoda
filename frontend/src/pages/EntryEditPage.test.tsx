/**
 * @jest-environment jsdom
 */

import {
  render,
  screen,
  act,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { createMemoryRouter, RouterProvider } from "react-router";

import { EntryEditPage } from "./EntryEditPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { entryEditPath, newEntryPath } from "routes/Routes";

const mockEntity = {
  id: 2,
  name: "test entity",
  note: "",
  isToplevel: false,
  attrs: [
    {
      id: 1,
      name: "attr1",
      type: 2, // string
      isMandatory: false,
      isDeleteInChain: false,
      isWritable: true,
      referral: [],
    },
  ],
  webhooks: [],
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
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("EntryEditPage", () => {
  beforeEach(() => {
    Object.defineProperty(window, "django_context", {
      value: {
        user: {
          is_superuser: false,
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
});
