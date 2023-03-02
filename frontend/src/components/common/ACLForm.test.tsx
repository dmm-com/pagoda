/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React, { FC } from "react";
import { useForm } from "react-hook-form";

import { Schema } from "../acl/ACLFormSchema";

import { ACLForm } from "components/common/ACLForm";
import { TestWrapper } from "services/TestWrapper";

test("should render a component with essential props", function () {
  const Wrapper: FC = () => {
    const { setValue, control, getValues } = useForm<Schema>({
      defaultValues: {
        isPublic: true,
        defaultPermission: 0,
        acl: [],
      },
    });

    return (
      <ACLForm
        aclInfo={{
          isPublic: true,
          defaultPermission: 0,
          permissions: {},
        }}
        setACLInfo={() => {
          /* no operation */
        }}
        setSubmittable={() => {
          /* no operation */
        }}
        control={control}
        getValues={getValues}
        watch={undefined}
      />
    );
  };

  expect(() =>
    render(<Wrapper />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
