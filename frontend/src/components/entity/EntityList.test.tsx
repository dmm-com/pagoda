/**
 * @jest-environment jsdom
 */

import { act, fireEvent, render, screen } from "@testing-library/react";

import { PaginatedEntityListList } from "@dmm-com/airone-apiclient-typescript-fetch";
import { TestWrapper } from "TestWrapper";
import { EntityList } from "components/entity/EntityList";

describe("EntityList", () => {
  const entities: PaginatedEntityListList = {
    count: 3,
    results: [
      {
        id: 1,
        name: "entity1",
        note: "entity1",
        isToplevel: false,
      },
      {
        id: 2,
        name: "entity2",
        note: "entity2",
        isToplevel: false,
      },
      {
        id: 3,
        name: "entity3",
        note: "entity3",
        isToplevel: false,
      },
    ],
  };

  test("should render entities", () => {
    const changePage = jest.fn();
    const handleChangeQuery = jest.fn();

    render(
      <EntityList
        entities={entities}
        page={1}
        query=""
        changePage={changePage}
        handleChangeQuery={handleChangeQuery}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByRole("link", { name: "entity1" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "entity2" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "entity3" })).toBeInTheDocument();

    // specify keyword
    act(() => {
      fireEvent.change(screen.getByPlaceholderText("モデルを絞り込む"), {
        target: { value: "entity" },
      });
      fireEvent.keyDown(screen.getByPlaceholderText("モデルを絞り込む"), {
        key: "Enter",
        code: "Enter",
        charCode: 13,
      });
    });
    expect(screen.getByPlaceholderText("モデルを絞り込む")).toHaveValue(
      "entity",
    );
    expect(handleChangeQuery).toBeCalled();
  });
});
