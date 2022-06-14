/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { BasicFields } from "./BasicFields";

import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <BasicFields
        entityInfo={{
          id: 1,
          name: "hoge",
          note: "fuga",
          isToplevel: false,
          attrs: [],
        }}
        setEntityInfo={() => {
          /* nothing */
        }}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
