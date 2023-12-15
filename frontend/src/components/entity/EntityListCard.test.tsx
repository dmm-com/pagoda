/**
 * @jest-environment jsdom
 */

import { EntityList } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { EntityListCard } from "components/entity/EntityListCard";

test("should render with essential props", () => {
  const entity: EntityList = {
    id: 1,
    name: "TestEntity",
    note: "This is a test entity.",
    isToplevel: true,
  };
  expect(() =>
    render(<EntityListCard entity={entity} />, { wrapper: TestWrapper })
  ).not.toThrow();
});
