/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React, { FC } from "react";
import { useForm } from "react-hook-form";

import { Schema } from "./aclForm/ACLFormSchema";

import { TestWrapper } from "TestWrapper";
import { ACLForm } from "components/acl/ACLForm";
import { ACLType } from "services/Constants";

test("should render a component with essential props", function () {
  const Wrapper: FC = () => {
    const { control, watch } = useForm<Schema>({
      defaultValues: {
        isPublic: true,
        defaultPermission: ACLType.Nothing,
        roles: [],
      },
    });

    return <ACLForm control={control} watch={watch} />;
  };

  expect(() =>
    render(<Wrapper />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
