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
import { GroupEditPage } from "pages/GroupEditPage";

const server = setupServer(
  // getGroup
  http.get("http://localhost/group/api/v2/groups/1", () => {
    return HttpResponse.json({
      id: 1,
      name: "group1",
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

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("EditGroupPage", () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        isSuperuser: true,
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
});
