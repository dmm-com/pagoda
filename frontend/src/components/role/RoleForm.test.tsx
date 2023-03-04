/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React, { FC } from "react";
import { useForm } from "react-hook-form";

import { TestWrapper } from "../../services/TestWrapper";

import { RoleForm } from "./RoleForm";
import { Schema } from "./RoleFormSchema";

test("should render a component with essential props", function () {
  const role: Schema = {
    id: 0,
    isActive: false,
    name: "",
    description: "",
    users: [],
    groups: [],
    adminUsers: [],
    adminGroups: [],
  };

  /* eslint-disable */
  jest
    .spyOn(require("apiclient/AironeApiClientV2").aironeApiClientV2, "getUsers")
    .mockResolvedValue(Promise.resolve([]));
  jest
    .spyOn(
      require("apiclient/AironeApiClientV2").aironeApiClientV2,
      "getGroups"
    )
    .mockResolvedValue(Promise.resolve([]));
  /* eslint-enable */

  const Wrapper: FC = () => {
    const { setValue, control } = useForm<Schema>({
      defaultValues: role,
    });
    return <RoleForm control={control} setValue={setValue} />;
  };

  expect(() =>
    render(<Wrapper />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
