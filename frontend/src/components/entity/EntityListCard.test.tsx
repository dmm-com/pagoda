/**
 * @jest-environment jsdom
 */

import { EntityList } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { EntityListCard } from "components/entity/EntityListCard";

describe("EntityListCard", () => {
  const entity: EntityList = {
    id: 1,
    name: "TestEntity",
    note: "This is a test entity.",
    isToplevel: true,
  };

  test("should render entity", () => {
    const setToggle = jest.fn();

    render(<EntityListCard entity={entity} setToggle={setToggle} />, {
      wrapper: TestWrapper,
    });

    expect(screen.getByText(entity.name)).toBeInTheDocument();
    expect(screen.getByText(entity?.note ?? "")).toBeInTheDocument();
  });
});
