/**
 * @jest-environment jsdom
 */

import { UserRetrieveAuthenticateTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod/dist/zod";
import { render, renderHook, screen } from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { TestWrapper } from "../../TestWrapper";
import { schema } from "../entry/entryForm/EntryFormSchema";

import { UserForm } from "./UserForm";
import { Schema } from "./userForm/UserFormSchema";

describe("UserForm", () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        is_superuser: false,
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
  };

  test("should provide user editor", function () {
    const {
      result: {
        current: { control },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues: userInfo,
      })
    );

    render(
      <UserForm
        user={userInfo}
        control={control}
        isCreateMode={true}
        isMyself={true}
        isSuperuser={false}
        isSubmittable={false}
        handleSubmit={() => Promise.resolve()}
        handleCancel={() => {
          /* do nothing */
        }}
      />,
      { wrapper: TestWrapper }
    );

    expect(
      screen.getByPlaceholderText("ユーザ名を入力してください")
    ).toHaveValue("user1");
    expect(
      screen.getByPlaceholderText("メールアドレスを入力してください")
    ).toHaveValue("user1@example.com");
    expect(
      screen.getByPlaceholderText("パスワードを入力してください")
    ).toHaveValue("user1");
  });
});
