/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { AttributesFields } from "./AttributesFields";

import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <AttributesFields
        attributes={[]}
        referralEntities={[]}
        setAttributes={() => {
          /* nothing */
        }}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
