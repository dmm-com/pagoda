/**
 * @jest-environment jsdom
 */

import React from "react";
import { render } from "@testing-library/react";

import EntityForm from "./EntityForm";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <EntityForm
        initName={""}
        initNote={""}
        initIsTopLevel={false}
        initAttributes={[]}
      />
    )
  ).not.toThrow();
});
