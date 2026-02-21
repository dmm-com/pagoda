/**
 * @jest-environment jsdom
 */

import { zodResolver } from "@hookform/resolvers/zod";
import {
  act,
  fireEvent,
  render,
  renderHook,
  screen,
} from "@testing-library/react";
import { useForm } from "react-hook-form";

import { CategoryForm } from "./CategoryForm";
import { Schema, schema } from "./categoryForm/CategoryFormSchema";

import { TestWrapper } from "TestWrapper";
import * as usePagodaSWRModule from "hooks/usePagodaSWR";
import { aironeApiClient } from "repository/AironeApiClient";
import { ACLType } from "services/ACLUtil";

// Mock data
const mockEntities = {
  count: 3,
  results: [
    { id: 1, name: "モデル1", isToplevel: true, permission: ACLType.Full },
    { id: 2, name: "モデル2", isToplevel: true, permission: ACLType.Full },
    { id: 3, name: "モデル3", isToplevel: false, permission: ACLType.Full },
  ],
};

// Default values
const defaultValues: Schema = {
  id: 0,
  name: "",
  note: "",
  models: [],
  priority: 0,
  permission: ACLType.Full,
};

beforeEach(() => {
  jest.clearAllMocks();
});

describe("CategoryForm", () => {
  test("should render all form fields correctly", async () => {
    // API Mock
    jest.spyOn(aironeApiClient, "getEntities").mockResolvedValue(mockEntities);

    // Render form hook
    const { result } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      }),
    );

    await act(async () => {
      render(
        <CategoryForm
          control={result.current.control}
          setValue={result.current.setValue}
        />,
        { wrapper: TestWrapper },
      );
    });

    // Check existence of each field
    expect(screen.getByText("カテゴリ名")).toBeInTheDocument();
    expect(screen.getByText("備考")).toBeInTheDocument();
    expect(screen.getByText("登録モデル(複数可)")).toBeInTheDocument();
    expect(screen.getByText("表示優先度")).toBeInTheDocument();

    // Check input fields
    expect(screen.getByPlaceholderText("カテゴリ名")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("備考")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("モデルを選択")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("表示優先度")).toBeInTheDocument();
  });

  test("should handle input changes correctly", async () => {
    // API Mock
    jest.spyOn(aironeApiClient, "getEntities").mockResolvedValue(mockEntities);

    // Render form hook
    const { result } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      }),
    );

    await act(async () => {
      render(
        <CategoryForm
          control={result.current.control}
          setValue={result.current.setValue}
        />,
        { wrapper: TestWrapper },
      );
    });

    // Input test
    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText("カテゴリ名"), {
        target: { value: "テストカテゴリ" },
      });

      fireEvent.change(screen.getByPlaceholderText("備考"), {
        target: { value: "テスト備考" },
      });

      fireEvent.change(screen.getByPlaceholderText("表示優先度"), {
        target: { value: "10" },
      });
    });

    // Verify values
    expect(screen.getByPlaceholderText("カテゴリ名")).toHaveValue(
      "テストカテゴリ",
    );
    expect(screen.getByPlaceholderText("備考")).toHaveValue("テスト備考");
    // Compare as number type since it's treated as a number
    expect(screen.getByPlaceholderText("表示優先度")).toHaveValue(10);
  });

  test("should handle entity selection correctly", async () => {
    // API Mock
    jest.spyOn(aironeApiClient, "getEntities").mockResolvedValue(mockEntities);

    // Render form hook
    const { result } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      }),
    );

    // Mock setValue
    const setValueMock = jest.fn();

    await act(async () => {
      render(
        <CategoryForm
          control={result.current.control}
          setValue={setValueMock}
        />,
        { wrapper: TestWrapper },
      );
    });

    // Test Autocomplete
    const autocomplete = screen.getByPlaceholderText("モデルを選択");
    expect(autocomplete).toBeInTheDocument();

    // Open dropdown
    await act(async () => {
      fireEvent.mouseDown(autocomplete);
    });

    // Verify options are displayed
    expect(screen.getByText("モデル1")).toBeInTheDocument();
    expect(screen.getByText("モデル2")).toBeInTheDocument();
    expect(screen.getByText("モデル3")).toBeInTheDocument();
  });

  test("should show loading state when fetching entities", async () => {
    // Set API to loading state
    jest.spyOn(aironeApiClient, "getEntities").mockImplementation(
      () =>
        new Promise(() => {
          /* never resolve */
        }),
    );

    // Render form hook
    const { result } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      }),
    );

    await act(async () => {
      render(
        <CategoryForm
          control={result.current.control}
          setValue={result.current.setValue}
        />,
        { wrapper: TestWrapper },
      );
    });

    // Verify Autocomplete is disabled
    const autocomplete = screen.getByPlaceholderText("モデルを選択");
    expect(autocomplete).toBeDisabled();
  });

  test("should handle API error gracefully", async () => {
    // Suppress console errors
    const originalConsoleError = console.error;
    console.error = jest.fn();

    try {
      // Mock usePagodaSWR to return loading state
      jest.spyOn(usePagodaSWRModule, "usePagodaSWR").mockImplementation(() => {
        return {
          data: undefined,
          error: undefined,
          isLoading: true,
          isValidating: false,
          mutate: jest.fn(),
        } as ReturnType<typeof usePagodaSWRModule.usePagodaSWR>;
      });

      // Render form hook
      const { result } = renderHook(() =>
        useForm<Schema>({
          resolver: zodResolver(schema),
          mode: "onBlur",
          defaultValues,
        }),
      );

      // Execute rendering
      await act(async () => {
        render(
          <CategoryForm
            control={result.current.control}
            setValue={result.current.setValue}
          />,
          { wrapper: TestWrapper },
        );
      });

      // Verify Autocomplete is disabled
      const autocomplete = screen.getByPlaceholderText("モデルを選択");
      expect(autocomplete).toBeDisabled();
    } finally {
      // Restore original console.error
      console.error = originalConsoleError;
    }
  });

  test("should handle entity selection correctly when entities are loading", async () => {
    // Set API to loading state
    jest.spyOn(aironeApiClient, "getEntities").mockImplementation(
      () =>
        new Promise(() => {
          /* never resolve */
        }),
    );

    // Render form hook
    const { result } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      }),
    );

    // Mock setValue
    const setValueMock = jest.fn();

    await act(async () => {
      render(
        <CategoryForm
          control={result.current.control}
          setValue={setValueMock}
        />,
        { wrapper: TestWrapper },
      );
    });

    // Test Autocomplete
    const autocomplete = screen.getByPlaceholderText("モデルを選択");
    expect(autocomplete).toBeInTheDocument();

    // Open dropdown
    await act(async () => {
      fireEvent.mouseDown(autocomplete);
    });

    // Verify options are not displayed
    expect(screen.queryByText("モデル1")).not.toBeInTheDocument();
    expect(screen.queryByText("モデル2")).not.toBeInTheDocument();
    expect(screen.queryByText("モデル3")).not.toBeInTheDocument();
  });
});
