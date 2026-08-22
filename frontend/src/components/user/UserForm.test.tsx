/**
 */

import {
  UserRetrieve,
  UserRetrieveAuthenticateTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { render, renderHook, screen } from "@testing-library/react";
import { useForm } from "react-hook-form";

import { TestWrapper } from "../../TestWrapper";
import { schema } from "../entry/entryForm/EntryFormSchema";

import { UserForm } from "./UserForm";
import { Schema } from "./userForm/UserFormSchema";

describe("UserForm", () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        username: "user1",
        isSuperuser: false,
      },
    },
    writable: false,
  });

  const userInfo = {
    id: 1,
    username: "user1",
    password: "user1",
    email: "user1@example.com",
    isSuperuser: false,
    dateJoined: "",
    token: {
      value: "",
      lifetime: 86400,
      expire: "",
      created: "",
    },
    authenticateType: UserRetrieveAuthenticateTypeEnum.AUTH_TYPE_LOCAL,
    groups: [],
    roles: [],
  };

  const renderUserForm = (user: UserRetrieve, isCreateMode: boolean) => {
    const {
      result: {
        current: { control },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues: user,
      }),
    );

    render(
      <UserForm
        user={user}
        control={control}
        isCreateMode={isCreateMode}
        isMyself={false}
        isSubmittable={false}
        isCoUser={false}
        handleSubmit={() => Promise.resolve()}
        handleCancel={() => {
          /* do nothing */
        }}
      />,
      { wrapper: TestWrapper },
    );
  };

  test("should provide user editor", function () {
    renderUserForm(userInfo, true);

    expect(
      screen.getByPlaceholderText("ユーザ名を入力してください"),
    ).toHaveValue("user1");
    expect(
      screen.getByPlaceholderText("パスワードを入力してください"),
    ).toHaveValue("user1");
    expect(screen.getByText("user1-")).toBeInTheDocument();
  });

  test("should not show belonging groups and roles on creating a user", function () {
    renderUserForm(userInfo, true);

    expect(screen.queryByText("所属グループ")).not.toBeInTheDocument();
    expect(screen.queryByText("所属ロール")).not.toBeInTheDocument();
  });

  test("should show belonging groups and roles", function () {
    renderUserForm(
      {
        ...userInfo,
        groups: [
          { id: 10, name: "child_group", isDirect: true },
          { id: 11, name: "parent_group", isDirect: false },
        ],
        roles: [
          {
            id: 20,
            name: "direct_role",
            isDirect: true,
            isAdmin: false,
            viaGroups: [],
          },
          {
            id: 21,
            name: "group_role",
            isDirect: false,
            isAdmin: false,
            viaGroups: [{ id: 10, name: "child_group" }],
          },
          {
            id: 22,
            name: "admin_role",
            isDirect: false,
            isAdmin: true,
            viaGroups: [{ id: 11, name: "parent_group" }],
          },
        ],
      },
      false,
    );

    // a Chip renders its label in an inner element, so the link is its ancestor
    const linkOf = (label: string) => screen.getByText(label).closest("a");

    expect(screen.getByText("所属グループ")).toBeInTheDocument();
    expect(linkOf("child_group")).toHaveAttribute("href", "/ui/groups/10");
    // an inherited group is annotated so that it's distinguishable
    expect(linkOf("parent_group (継承)")).toHaveAttribute(
      "href",
      "/ui/groups/11",
    );

    expect(screen.getByText("所属ロール")).toBeInTheDocument();
    expect(linkOf("direct_role")).toHaveAttribute("href", "/ui/roles/20");
    expect(linkOf("group_role (child_group 経由)")).toHaveAttribute(
      "href",
      "/ui/roles/21",
    );
    expect(linkOf("admin_role (管理 / parent_group 経由)")).toHaveAttribute(
      "href",
      "/ui/roles/22",
    );
  });

  test("should show placeholders when the user belongs to nothing", function () {
    renderUserForm({ ...userInfo, groups: [], roles: [] }, false);

    expect(
      screen.getByText("所属しているグループはありません"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("所属しているロールはありません"),
    ).toBeInTheDocument();
  });
});
