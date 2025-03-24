/**
 * @jest-environment jsdom
 */

import { act, render, screen } from "@testing-library/react";
import React from "react";

import { CategoryList } from "./CategoryList";

import { TestWrapper } from "TestWrapper";
import { aironeApiClient } from "repository/AironeApiClient";

// Setup API mocks
beforeEach(() => {
  jest.clearAllMocks();
});

describe("CategoryList", () => {
  test("should render with categories when isEdit is false", async () => {
    // Mock API response
    const getCategoriesMock = jest
      .spyOn(aironeApiClient, "getCategories")
      .mockResolvedValue({
        count: 2,
        results: [
          {
            id: 1,
            name: "テストカテゴリ1",
            models: [
              { id: 101, name: "モデル1" },
              { id: 102, name: "モデル2" },
            ],
            note: "",
            priority: 0,
          },
          {
            id: 2,
            name: "テストカテゴリ2",
            models: [{ id: 201, name: "モデル3" }],
            note: "",
            priority: 0,
          },
        ],
      });

    await act(async () => {
      render(<CategoryList isEdit={false} />, {
        wrapper: TestWrapper,
      });
    });

    // Verify API was called correctly
    expect(getCategoriesMock).toHaveBeenCalledWith(1, "");

    // Verify category names are displayed
    expect(screen.getByText("テストカテゴリ1")).toBeInTheDocument();
    expect(screen.getByText("テストカテゴリ2")).toBeInTheDocument();

    // Verify model names are displayed
    expect(screen.getByText("モデル1")).toBeInTheDocument();
    expect(screen.getByText("モデル2")).toBeInTheDocument();
    expect(screen.getByText("モデル3")).toBeInTheDocument();

    // Verify create button is not displayed
    expect(screen.queryByText("新規カテゴリを作成")).not.toBeInTheDocument();

    // Verify pagination is displayed
    expect(screen.getByText("1 - 2 / 2 件")).toBeInTheDocument();
  });

  test("should render with categories when isEdit is true", async () => {
    // Mock API response
    jest.spyOn(aironeApiClient, "getCategories").mockResolvedValue({
      count: 1,
      results: [
        {
          id: 1,
          name: "テストカテゴリ1",
          models: [{ id: 101, name: "モデル1" }],
          note: "",
          priority: 0,
        },
      ],
    });

    await act(async () => {
      render(<CategoryList isEdit={true} />, {
        wrapper: TestWrapper,
      });
    });

    // Verify create button is displayed
    expect(screen.getByText("新規カテゴリを作成")).toBeInTheDocument();
  });

  test("should render loading state", async () => {
    // Delay API response to show loading state
    jest.spyOn(aironeApiClient, "getCategories").mockImplementation(
      () =>
        new Promise(() => {
          // Never resolve to keep loading state
          // This test only verifies the loading state,
          // so we don't need to resolve the promise
        }),
    );

    render(<CategoryList />, {
      wrapper: TestWrapper,
    });

    // Verify loading indicator is displayed
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  test("should render empty state", async () => {
    // Mock API with empty results
    jest.spyOn(aironeApiClient, "getCategories").mockResolvedValue({
      count: 0,
      results: [],
    });

    await act(async () => {
      render(<CategoryList />, {
        wrapper: TestWrapper,
      });
    });

    // Verify no categories are displayed
    expect(screen.queryByText(/テストカテゴリ/)).not.toBeInTheDocument();

    // Verify pagination shows zero items
    expect(screen.getByText("0 - 0 / 0 件")).toBeInTheDocument();
  });
});
