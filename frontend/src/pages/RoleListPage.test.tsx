/**
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { RoleListPage } from "./RoleListPage";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

const server = setupServer(
  // getRoles
  http.get("*/role/api/v2/", () => {
    return HttpResponse.json([
      {
        id: 1,
        name: "role1",
        description: "role1",
        users: [],
        groups: [],
        admin_users: [],
        admin_groups: [],
        is_editable: true,
      },
    ]);
  }),
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("RoleListPage", () => {
  test("should match snapshot", async () => {
    // wait async calls and get rendered fragment
    let result: ReturnType<typeof render>;
    await act(async () => {
      result = render(<RoleListPage />, {
        wrapper: TestWrapper,
      });
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(result!).toMatchSnapshot();
  });

  test("links to registered users and groups in new tabs", async () => {
    server.use(
      http.get("*/role/api/v2/", () =>
        HttpResponse.json([
          {
            id: 1,
            name: "role1",
            description: "role1",
            users: [{ id: 11, username: "member-user" }],
            groups: [{ id: 21, name: "member-group" }],
            admin_users: [{ id: 12, username: "admin-user" }],
            admin_groups: [{ id: 22, name: "admin-group" }],
            is_editable: true,
          },
        ]),
      ),
    );

    await act(async () => {
      render(<RoleListPage />, { wrapper: TestWrapper });
    });

    const links = [
      ["member-user", "/ui/users/11"],
      ["member-group", "/ui/groups/21"],
      ["admin-user", "/ui/users/12"],
      ["admin-group", "/ui/groups/22"],
    ] as const;

    for (const [name, href] of links) {
      const link = await screen.findByRole("link", { name });
      expect(link).toHaveAttribute("href", href);
      expect(link).toHaveAttribute("target", "_blank");
    }
  });

  test("renders in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });

    await act(async () => {
      render(<RoleListPage />, {
        wrapper: TestWrapper,
      });
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });

    expect(screen.getAllByText("Role management").length).toBeGreaterThan(0);
  });
});
