/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { UserForm } from "components/user/UserForm";
import { TestWrapper } from "services/TestWrapper";

test("should render a component with essential props", function () {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        is_superuser: false,
      },
    },
    writable: false,
  });

  const userInfo = {
    id: 0,
    username: "",
    password: "",
    email: "",
    isSuperuser: false,
    dateJoined: "",
    token: {
      value: "",
      lifetime: 86400,
      expire: "",
      created: "",
    },
    authenticateType: 0,
  };

  const setUserInfo = () => {
    /* do nothing */
  };

  expect(() =>
    render(
      <UserForm
        userInfo={userInfo}
        setUserInfo={setUserInfo}
        handleSubmit={() => { }}
        handleCancel={() => { }}
      />,
      {
        wrapper: TestWrapper,
      }
    )
  ).not.toThrow();
});
