import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { RoleHistoryPage } from "./RoleHistoryPage";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { aironeApiClient, RoleHistoryRecord } from "repository/AironeApiClient";

const history: RoleHistoryRecord = {
  history_id: 2,
  history_source: "role",
  history_date: "2026-11-05T00:00:00Z",
  history_user: "admin",
  history_type: "~",
  history_change_reason: "Job #123",
  name: "role",
  description: "description",
  is_active: true,
  relations: {
    users: [{ id: 1, username: "member" }],
    permissions: [
      { id: 2, codename: "10.2", name: "Server model" },
      { id: 3, codename: "11.4", name: "Server item" },
      { id: 4, codename: "12.8", name: "Owner model" },
    ],
  },
};

const setup = (page = 1, source: "role" | "permission" = "role") => {
  vi.spyOn(aironeApiClient, "getRoleHistories").mockResolvedValue({
    role: { id: 1, name: "role", is_active: true, is_editable: true },
    count: 12,
    results: [history, { ...history, history_id: 1, history_source: source }],
  });
  const restore = vi
    .spyOn(aironeApiClient, "restoreRoleHistory")
    .mockResolvedValue();
  const router = createMemoryRouter(
    [
      { path: "/ui/roles/:roleId/history", element: <RoleHistoryPage /> },
      { path: "/ui/roles", element: <div>Roles</div> },
    ],
    { initialEntries: [`/ui/roles/1/history?page=${page}`] },
  );
  render(<RouterProvider router={router} />, {
    wrapper: TestWrapperWithoutRoutes,
  });
  return { router, restore };
};

afterEach(() => vi.restoreAllMocks());

test("shows actor, job and relations, and restores after confirmation", async () => {
  const { router, restore } = setup();
  const buttons = await screen.findAllByRole("button", { name: "復旧" });
  expect(screen.getAllByText("member", { exact: false })).toHaveLength(2);
  expect(screen.getAllByText("Job #123")).toHaveLength(2);
  expect(screen.getAllByText(/Server model：閲覧/)).toHaveLength(2);
  expect(screen.getAllByText(/Server item：閲覧・編集/)).toHaveLength(2);
  expect(screen.getAllByText(/Owner model：閲覧・編集・削除/)).toHaveLength(2);
  expect(screen.queryByText(/10\.2/)).not.toBeInTheDocument();
  expect(buttons[0]).toBeDisabled();
  fireEvent.click(buttons[1]!);
  expect(restore).not.toHaveBeenCalled();
  fireEvent.click(await screen.findByRole("button", { name: "Yes" }));
  await waitFor(() => expect(restore).toHaveBeenCalledWith(1, 1, "role"));
  await waitFor(() => expect(router.state.location.pathname).toBe("/ui/roles"));
});

test("allows restoring the first row on later pages", async () => {
  setup(2);
  const buttons = await screen.findAllByRole("button", { name: "復旧" });
  expect(buttons[0]).toBeEnabled();
  expect(aironeApiClient.getRoleHistories).toHaveBeenCalledWith(1, 2);
});

test("restores a permission event with its own history source", async () => {
  const { restore } = setup(1, "permission");
  const buttons = await screen.findAllByRole("button", { name: "復旧" });
  fireEvent.click(buttons[1]!);
  fireEvent.click(await screen.findByRole("button", { name: "Yes" }));
  await waitFor(() => expect(restore).toHaveBeenCalledWith(1, 1, "permission"));
});
