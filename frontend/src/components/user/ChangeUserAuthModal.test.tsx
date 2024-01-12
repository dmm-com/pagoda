/**
 * @jest-environment jsdom
 */

import {
  UserRetrieve,
  UserRetrieveAuthenticateTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../TestWrapper";

import { ChangeUserAuthModal } from "./ChangeUserAuthModal";

describe("ChangeUserAuthModal", () => {
  const user: UserRetrieve = {
    id: 1,
    username: "user1",
    email: "email",
    isSuperuser: false,
    dateJoined: "2021-01-01T00:00:00+09:00",
    token: {
      value: "",
      lifetime: 86400,
      expire: "",
      created: "",
    },
    authenticateType: UserRetrieveAuthenticateTypeEnum.AUTH_TYPE_LOCAL,
  };

  test("should render a component essentially", async () => {
    const closeModal = jest.fn();

    render(
      <ChangeUserAuthModal
        user={user}
        openModal={true}
        closeModal={closeModal}
      />,
      {
        wrapper: TestWrapper,
      }
    );

    expect(
      screen.getByText(user.username, { exact: false })
    ).toBeInTheDocument();

    await waitFor(() => {
      screen.getByRole("button", { name: "キャンセル" }).click();
    });

    expect(closeModal).toHaveBeenCalled();
  });

  test("should handle a success on updating auth method", async () => {
    /* eslint-disable */
    jest
      .spyOn(
        require("repository/AironeApiClient").aironeApiClient,
        "updateUserAuth"
      )
      .mockResolvedValue(Promise.resolve());
    /* eslint-enable */

    render(
      <ChangeUserAuthModal
        user={user}
        openModal={true}
        closeModal={jest.fn()}
      />,
      {
        wrapper: TestWrapper,
      }
    );

    await waitFor(() => {
      screen.getByRole("button", { name: "送信" }).click();
    });

    expect(
      screen.queryByText("認証方法の変更に成功しました")
    ).not.toBeInTheDocument();
  });

  test("should handle a failure on updating auth method", async () => {
    /* eslint-disable */
    jest
      .spyOn(
        require("repository/AironeApiClient").aironeApiClient,
        "updateUserAuth"
      )
      .mockResolvedValue(Promise.reject());
    /* eslint-enable */

    render(
      <ChangeUserAuthModal
        user={user}
        openModal={true}
        closeModal={jest.fn()}
      />,
      {
        wrapper: TestWrapper,
      }
    );

    await waitFor(() => {
      screen.getByRole("button", { name: "送信" }).click();
    });

    expect(
      screen.queryByText("認証方法の変更に失敗しました")
    ).not.toBeInTheDocument();
  });
});
