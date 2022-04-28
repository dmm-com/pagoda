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
          name: "hoge",
          note: "fuga",
          isTopLevel: false,
          attributes: [],
        }}
        setEntityInfo={() => {
          /* nothing */
        }}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
