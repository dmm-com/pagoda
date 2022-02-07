/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntryList } from "components/entry/EntryList";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(<EntryList entityId={"0"} entries={[]} restoreMode={false} />, {
      wrapper: TestWrapper,
    })
  ).not.toThrow();
});
