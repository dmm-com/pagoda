/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { AutoCompletedField } from "./AutoCompletedField";

import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <AutoCompletedField
        options={["o1", "o2"]}
        getOptionLabel={(option: string) => option}
        handleChangeSelectedValue={() => {
          /* nothing */
        }}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
