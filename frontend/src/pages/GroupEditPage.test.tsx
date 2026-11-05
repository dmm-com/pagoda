/**
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
import { ReactNode, useEffect } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { useSWRConfig } from "swr";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import i18n from "i18n/config";
import { GroupEditPage } from "pages/GroupEditPage";
import { aironeApiClient } from "repository/AironeApiClient";

const server = setupServer(
  // getGroup
  http.get("http://localhost/group/api/v2/groups/1", () => {
    return HttpResponse.json({
      id: 1,
      name: "group1",
      display_name: "表示名1",
      members: [
        {
          id: 1,
          username: "user1",
        },
      ],
      parent_group: null,
    });
  }),
  // getGroupTrees
  http.get("http://localhost/group/api/v2/groups/tree", () => {
    return HttpResponse.json([
      {
        id: 1,
        name: "group1",
        children: [
          {
            id: 1,
            name: "group1",
            children: [],
          },
          {
            id: 2,
            name: "group2",
            children: [],
          },
        ],
      },
      {
        id: 2,
        name: "group2",
        children: [],
      },
    ]);
  }),
  // getUsers
  http.get("http://localhost/user/api/v2/", () => {
    return HttpResponse.json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          username: "user1",
          email: "user1@example.com",
          is_superuser: false,
        },
        {
          id: 2,
          username: "user2",
          email: "user2@example.com",
          is_superuser: false,
        },
      ],
    });
  }),
);

beforeAll(() => server.listen());

afterEach(() => {
  server.resetHandlers();
  vi.restoreAllMocks();
});

afterAll(() => server.close());

describe("EditGroupPage", () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        id: 1,
        username: "admin",
        isSuperuser: true,
        isReadonly: false,
        parentUser: null,
        email: "admin@example.com",
      },
    },
    writable: false,
  });

  test("should match snapshot", async () => {
    const router = createMemoryRouter([
      {
        path: "/",
        element: <GroupEditPage />,
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

  test("keeps dirty form values when the fetched group is revalidated", async () => {
    let revalidate: (() => Promise<unknown>) | null = null;
    const RevalidationProbe = (): ReactNode => {
      const { mutate } = useSWRConfig();
      useEffect(() => {
        revalidate = () => mutate(["group", 1]);
      }, [mutate]);
      return null;
    };

    const router = createMemoryRouter(
      [
        {
          path: "/groups/:groupId",
          element: <GroupEditPage />,
        },
      ],
      { initialEntries: ["/groups/1"] },
    );
    render(
      <>
        <RouterProvider router={router} />
        <RevalidationProbe />
      </>,
      { wrapper: TestWrapperWithoutRoutes },
    );
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    // The fetched group name is synced into the form
    const getNameInputValue = () =>
      (screen.getByPlaceholderText("グループ名") as HTMLInputElement).value;
    await waitFor(() => {
      expect(getNameInputValue()).toBe("group1");
    });

    // Edit a field without saving
    fireEvent.change(screen.getByPlaceholderText("グループ名"), {
      target: { value: "edited" },
    });
    expect(getNameInputValue()).toBe("edited");

    // A background refetch replaces data with a new object identity,
    // but must not clobber the unsaved user edit.
    await act(async () => {
      await revalidate?.();
    });

    expect(getNameInputValue()).toBe("edited");
  });

  test("loads and submits the display name for an existing group", async () => {
    const updateGroup = vi
      .spyOn(aironeApiClient, "updateGroup")
      .mockResolvedValue();
    const router = createMemoryRouter(
      [
        {
          path: "/groups/:groupId",
          element: <GroupEditPage />,
        },
      ],
      { initialEntries: ["/groups/1"] },
    );

    render(<RouterProvider router={router} />, {
      wrapper: TestWrapperWithoutRoutes,
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    const displayNameInput = screen.getByPlaceholderText(
      "表示名（未設定時はグループ名）",
    );
    expect(displayNameInput).toHaveValue("表示名1");

    fireEvent.change(displayNameInput, { target: { value: "変更後の表示名" } });
    fireEvent.click(screen.getByRole("button", { name: "保存" }));

    await waitFor(() => {
      expect(updateGroup).toHaveBeenCalledWith(
        1,
        expect.objectContaining({ displayName: "変更後の表示名" }),
      );
    });
  });

  test("includes the display name when creating a group", async () => {
    const createGroup = vi
      .spyOn(aironeApiClient, "createGroup")
      .mockResolvedValue();
    const router = createMemoryRouter([
      {
        path: "/",
        element: <GroupEditPage />,
      },
    ]);

    render(<RouterProvider router={router} />, {
      wrapper: TestWrapperWithoutRoutes,
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText("グループ名"), {
      target: { value: "new-group" },
    });
    fireEvent.blur(screen.getByPlaceholderText("グループ名"));
    fireEvent.change(
      screen.getByPlaceholderText("表示名（未設定時はグループ名）"),
      { target: { value: "新規表示名" } },
    );
    fireEvent.blur(
      screen.getByPlaceholderText("表示名（未設定時はグループ名）"),
    );
    const saveButton = screen.getByRole("button", { name: "保存" });
    await waitFor(() => expect(saveButton).not.toBeDisabled());
    await act(async () => {
      fireEvent.click(saveButton);
    });

    await waitFor(() => {
      expect(createGroup).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "new-group",
          displayName: "新規表示名",
        }),
      );
    });
  });

  test("renders in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });

    const router = createMemoryRouter([
      {
        path: "/",
        element: <GroupEditPage />,
      },
    ]);
    await act(async () => {
      render(<RouterProvider router={router} />, {
        wrapper: TestWrapperWithoutRoutes,
      });
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(screen.getAllByText("Create a new group").length).toBeGreaterThan(0);
  });
});
