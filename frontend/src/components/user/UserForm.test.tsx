/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React, { FC } from "react";
import { useForm } from "react-hook-form";

import { TestWrapper } from "../../TestWrapper";

import { UserForm } from "./UserForm";
import { Schema } from "./UserFormSchema";

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

  const Wrapper: FC = () => {
    const { control } = useForm<Schema>({
      defaultValues: userInfo,
    });
    return (
      <UserForm
        user={userInfo}
        control={control}
        isCreateMode={true}
        isMyself={true}
        isSuperuser={false}
        isSubmittable={false}
        handleSubmit={(_e) => Promise.resolve()}
        handleCancel={() => {}}
      />
    );
  };

  expect(() =>
    render(<Wrapper />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
