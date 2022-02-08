/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ImportForm } from "components/common/ImportForm";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <ImportForm
        importFunc={() => Promise.resolve(new Response())}
        redirectPath={"/path/to/redirect"}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
