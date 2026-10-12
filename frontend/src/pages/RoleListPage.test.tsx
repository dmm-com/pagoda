/**
 */

import { act, render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { RoleListPage } from "./RoleListPage";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

const server = setupServer(
  // getRoles
  http.get("http://localhost/role/api/v2/", () => {
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

    expect(result!).toMatchSnapshot();
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

    expect(screen.getAllByText("Role management").length).toBeGreaterThan(0);
  });
});
