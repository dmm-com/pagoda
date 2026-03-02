/**
 * @jest-environment jsdom
 */

import {
  act,
  render,
  screen,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { TestWrapper } from "TestWrapper";
import { EntityListPage } from "pages/EntityListPage";
import { ACLType } from "services/ACLUtil";

const mockEntities = {
  count: 3,
  next: null,
  previous: null,
  results: [
    {
      id: 1,
      name: "Entity A",
      note: "Test note for entity A",
      is_toplevel: true,
      attrs: [],
      permission: ACLType.Full,
    },
    {
      id: 2,
      name: "Entity B",
      note: "",
      is_toplevel: false,
      attrs: [],
      permission: ACLType.Full,
    },
    {
      id: 3,
      name: "Entity C",
      note: "",
      is_toplevel: false,
      attrs: [],
      permission: ACLType.Full,
    },
  ],
};

const server = setupServer(
  http.get("http://localhost/entity/api/v2/", () => {
    return HttpResponse.json(mockEntities);
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("EntityListPage", () => {
  const renderPage = async () => {
    await act(async () => {
      render(<EntityListPage />, { wrapper: TestWrapper });
    });
  };

  test("should match snapshot", async () => {
    let result: ReturnType<typeof render>;
    await act(async () => {
      result = render(<EntityListPage />, {
        wrapper: TestWrapper,
      });
    });

    expect(result!).toMatchSnapshot();
  });

  describe("rendering", () => {
    test("should render page header with title", async () => {
      await renderPage();

      const titles = screen.getAllByText("モデル一覧");
      expect(titles.length).toBeGreaterThan(0);
    });

    test("should render breadcrumbs with Top link", async () => {
      await renderPage();

      expect(screen.getByText("Top")).toBeInTheDocument();
    });

    test("should render entity names from API response", async () => {
      await renderPage();

      expect(screen.getByText("Entity A")).toBeInTheDocument();
      expect(screen.getByText("Entity B")).toBeInTheDocument();
      expect(screen.getByText("Entity C")).toBeInTheDocument();
    });
  });

  describe("export/import buttons", () => {
    test("should render export button", async () => {
      await renderPage();

      expect(
        screen.getByRole("button", { name: /エクスポート/i }),
      ).toBeInTheDocument();
    });

    test("should render import button", async () => {
      await renderPage();

      expect(
        screen.getByRole("button", { name: /インポート/i }),
      ).toBeInTheDocument();
    });

    test("should open import modal when import button is clicked", async () => {
      await renderPage();

      const importButton = screen.getByRole("button", { name: /インポート/i });
      fireEvent.click(importButton);

      await waitFor(() => {
        expect(screen.getByText("モデルのインポート")).toBeInTheDocument();
      });
    });
  });

  describe("loading state", () => {
    test("should show loading indicator while fetching entities", () => {
      server.use(
        http.get("http://localhost/entity/api/v2/", async () => {
          await new Promise((resolve) => setTimeout(resolve, 500));
          return HttpResponse.json(mockEntities);
        }),
      );

      render(<EntityListPage />, { wrapper: TestWrapper });

      expect(screen.getByTestId("loading")).toBeInTheDocument();
    });
  });

  describe("empty state", () => {
    test("should render empty list when no entities returned", async () => {
      server.use(
        http.get("http://localhost/entity/api/v2/", () => {
          return HttpResponse.json({
            count: 0,
            next: null,
            previous: null,
            results: [],
          });
        }),
      );

      await act(async () => {
        render(<EntityListPage />, { wrapper: TestWrapper });
      });

      expect(screen.queryByText("Entity A")).not.toBeInTheDocument();
    });
  });

  describe("entity links", () => {
    test("should render entity names as links", async () => {
      await renderPage();

      const entityLink = screen.getByText("Entity A").closest("a");
      expect(entityLink).toHaveAttribute("href");
    });
  });
});
