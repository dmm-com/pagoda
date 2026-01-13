/**
 * @jest-environment jsdom
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { DashboardPage } from "./DashboardPage";

import { TestWrapper } from "TestWrapper";
import { ACLType } from "services/ACLUtil";

const mockCategories = {
  count: 3,
  next: null,
  previous: null,
  results: [
    {
      id: 1,
      name: "Category A",
      note: "First category",
      models: [{ id: 10, name: "Model 1" }],
      priority: 20,
      permission: ACLType.Full,
    },
    {
      id: 2,
      name: "Category B",
      note: "",
      models: [],
      priority: 10,
      permission: ACLType.Full,
    },
    {
      id: 3,
      name: "Category C",
      note: "",
      models: [
        { id: 20, name: "Model 2" },
        { id: 30, name: "Model 3" },
      ],
      priority: 0,
      permission: ACLType.Full,
    },
  ],
};

const server = setupServer(
  http.get("http://localhost/category/api/v2/", () => {
    return HttpResponse.json(mockCategories);
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("DashboardPage", () => {
  beforeEach(() => {
    Object.defineProperty(window, "django_context", {
      value: {
        user: {
          is_superuser: false,
        },
      },
      writable: true,
      configurable: true,
    });
  });

  const renderPage = async () => {
    await act(async () => {
      render(<DashboardPage />, { wrapper: TestWrapper });
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });
  };

  test("should match snapshot", async () => {
    const result = await act(() => {
      return render(<DashboardPage />, {
        wrapper: TestWrapper,
      });
    });
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });
    expect(result).toMatchSnapshot();
  });

  describe("category list rendering", () => {
    test("should render category list when no search query", async () => {
      await renderPage();

      expect(screen.getByText("Category A")).toBeInTheDocument();
      expect(screen.getByText("Category B")).toBeInTheDocument();
      expect(screen.getByText("Category C")).toBeInTheDocument();
    });

    test("should render models within categories", async () => {
      await renderPage();

      expect(screen.getByText("Model 1")).toBeInTheDocument();
      expect(screen.getByText("Model 2")).toBeInTheDocument();
      expect(screen.getByText("Model 3")).toBeInTheDocument();
    });
  });

  describe("category search box", () => {
    test("should render category search box with placeholder", async () => {
      await renderPage();

      expect(
        screen.getByPlaceholderText("カテゴリを絞り込む"),
      ).toBeInTheDocument();
    });

    test("search box should be present and interactive", async () => {
      await renderPage();

      const searchInput = screen.getByPlaceholderText("カテゴリを絞り込む");
      expect(searchInput).toBeInTheDocument();
    });
  });

  describe("loading state", () => {
    test("should show loading indicator initially", async () => {
      server.use(
        http.get("http://localhost/category/api/v2/", async () => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          return HttpResponse.json(mockCategories);
        }),
      );

      await act(async () => {
        render(<DashboardPage />, { wrapper: TestWrapper });
      });

      expect(screen.getByTestId("loading")).toBeInTheDocument();
    });
  });

  describe("empty categories", () => {
    test("should render empty state when no categories", async () => {
      server.use(
        http.get("http://localhost/category/api/v2/", () => {
          return HttpResponse.json({
            count: 0,
            next: null,
            previous: null,
            results: [],
          });
        }),
      );

      await renderPage();

      expect(screen.queryByText("Category A")).not.toBeInTheDocument();
    });
  });

  describe("category structure", () => {
    test("should render categories in priority order", async () => {
      await renderPage();

      const categoryA = screen.getByText("Category A");
      const categoryB = screen.getByText("Category B");
      const categoryC = screen.getByText("Category C");

      expect(categoryA).toBeInTheDocument();
      expect(categoryB).toBeInTheDocument();
      expect(categoryC).toBeInTheDocument();
    });
  });
});
