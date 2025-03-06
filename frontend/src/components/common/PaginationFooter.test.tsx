/**
 * @jest-environment jsdom
 */

import { act, render, screen } from "@testing-library/react";
import React from "react";

import { PaginationFooter } from "./PaginationFooter";

import { TestWrapper } from "TestWrapper";

describe("PaginationFooter", () => {
  const changePage = jest.fn();

  const cases: Array<{
    count: number;
    maxRowCount: number;
    page: number;
    expected: string;
  }> = [
    {
      count: 70,
      maxRowCount: 30,
      page: 1,
      expected: "1 - 30 / 70 件",
    },
    {
      count: 70,
      maxRowCount: 30,
      page: 2,
      expected: "31 - 60 / 70 件",
    },
    {
      count: 70,
      maxRowCount: 30,
      page: 3,
      expected: "61 - 70 / 70 件",
    },
    {
      count: 0,
      maxRowCount: 30,
      page: 1,
      expected: "0 - 0 / 0 件",
    },
  ];

  cases.forEach((c, i) =>
    test(`check number of items ${i}`, () => {
      render(
        <PaginationFooter
          count={c.count}
          maxRowCount={c.maxRowCount}
          page={c.page}
          changePage={changePage}
        />,
        { wrapper: TestWrapper },
      );

      expect(screen.getByText(c.expected)).toBeInTheDocument();
    }),
  );

  test("check change page handler", () => {
    render(
      <PaginationFooter
        count={1000}
        maxRowCount={30}
        page={1}
        changePage={changePage}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByRole("button", { name: "page 1" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Go to page 2" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Go to page 3" }),
    ).toBeInTheDocument();
    expect(screen.getByText("…")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Go to page 34" }),
    ).toBeInTheDocument();

    // change page
    act(() => {
      screen.getByRole("button", { name: "Go to page 2" }).click();
    });
    expect(changePage).toHaveBeenCalledWith(2);
  });

  test("check current page number", () => {
    render(
      <PaginationFooter
        count={1000}
        maxRowCount={30}
        page={2}
        changePage={changePage}
      />,
      { wrapper: TestWrapper },
    );

    expect(
      screen.getByRole("button", { name: "Go to page 1" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "page 2" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Go to page 3" }),
    ).toBeInTheDocument();
    expect(screen.getByText("…")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Go to page 34" }),
    ).toBeInTheDocument();
  });
});
