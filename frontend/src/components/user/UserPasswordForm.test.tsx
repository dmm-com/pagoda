/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { UserPasswordForm } from "components/user/UserPasswordForm";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  const user = {
    id: 1,
    username: "test",
    dateJoined: "",
    token: null,
  };

  expect(() =>
    render(<UserPasswordForm user={user} asSuperuser={true} />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
