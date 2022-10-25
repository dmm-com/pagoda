/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ACLForm } from "components/common/ACLForm";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
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
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
