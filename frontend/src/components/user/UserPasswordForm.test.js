/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import { UserPasswordForm } from "./UserPasswordForm";

test("should render a component with essential props", function () {
  const user = {
    id: 1,
    username: "test",
  };

  expect(() =>
    render(<UserPasswordForm user={user} asSuperuser={true} />)
  ).not.toThrow();
});
