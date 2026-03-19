/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { Header } from "./Header";

import { TestWrapper } from "TestWrapper";

// Mock ServerContext - configurable per test
const defaultServerContext = {
  title: "Airone",
  version: "1.0.0",
  headerColor: "#1976d2",
  legacyUiDisabled: true,
  extendedHeaderMenus: [] as Array<{
    name: string;
    children: Array<{ name: string; url: string }>;
  }>,
  user: { id: 1, username: "testuser" },
};

let mockServerContext = { ...defaultServerContext };

jest.mock("../../services/ServerContext", () => ({
  ServerContext: {
    getInstance: () => mockServerContext,
  },
}));

// Mock useTranslation
jest.mock("../../hooks/useTranslation", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        categories: "Categories",
        entities: "Entities",
        advancedSearch: "Advanced Search",
        management: "Management",
        manageUsers: "Users",
        manageGroups: "Groups",
        manageRoles: "Roles",
        manageTriggers: "Triggers",
        previousVersion: "Previous Version",
        currentUser: "(current user)",
        userSetting: "User Settings",
        logout: "Logout",
        noRunningJobs: "No running jobs",
        jobs: "Jobs",
      };
      return translations[key] || key;
    },
    i18n: { language: "en" },
    ready: true,
  }),
}));

// Mock useSimpleSearch
jest.mock("../../hooks/useSimpleSearch", () => ({
  useSimpleSearch: () => [undefined, jest.fn()],
}));

// Mock aironeApiClient
jest.mock("../../repository/AironeApiClient", () => ({
  aironeApiClient: {
    getRecentJobs: jest.fn().mockResolvedValue([]),
  },
}));

// Mock useInterval
jest.mock("../../hooks/useInterval", () => ({
  useInterval: jest.fn(),
}));

describe("Header", () => {
  beforeEach(() => {
    mockServerContext = { ...defaultServerContext, extendedHeaderMenus: [] };
  });

  describe("rendering", () => {
    test("should render header with title", () => {
      render(<Header />, { wrapper: TestWrapper });

      expect(screen.getByText("Airone")).toBeInTheDocument();
    });

    test("should render version", () => {
      render(<Header />, { wrapper: TestWrapper });

      expect(screen.getByText("1.0.0")).toBeInTheDocument();
    });

    test("should render navigation buttons", () => {
      render(<Header />, { wrapper: TestWrapper });

      expect(screen.getByText("Categories")).toBeInTheDocument();
      expect(screen.getByText("Entities")).toBeInTheDocument();
      expect(screen.getByText("Advanced Search")).toBeInTheDocument();
      expect(screen.getByText("Management")).toBeInTheDocument();
    });

    test("should render search box", () => {
      render(<Header />, { wrapper: TestWrapper });

      expect(screen.getByPlaceholderText("Search")).toBeInTheDocument();
    });
  });

  describe("user menu", () => {
    test("should show user menu when user icon is clicked", async () => {
      render(<Header />, { wrapper: TestWrapper });

      // Find the user icon button (PersonIcon)
      const buttons = screen.getAllByRole("button");
      const userButton = buttons.find((btn) =>
        btn.querySelector('svg[data-testid="PersonIcon"]'),
      );

      if (userButton) {
        fireEvent.click(userButton);

        await waitFor(() => {
          expect(screen.getByText(/testuser/)).toBeInTheDocument();
        });
      }
    });
  });

  describe("job menu", () => {
    test("should show job menu when job icon is clicked", async () => {
      render(<Header />, { wrapper: TestWrapper });

      const buttons = screen.getAllByRole("button");
      const jobButton = buttons.find((btn) =>
        btn.querySelector('svg[data-testid="TaskIcon"]'),
      );

      if (jobButton) {
        fireEvent.click(jobButton);

        await waitFor(() => {
          expect(screen.getByText("No running jobs")).toBeInTheDocument();
        });
      }
    });
  });

  describe("management menu", () => {
    test("should show management submenu on hover", async () => {
      render(<Header />, { wrapper: TestWrapper });

      const managementButton = screen.getByText("Management");
      fireEvent.mouseEnter(managementButton);

      await waitFor(() => {
        expect(screen.getByText("Users")).toBeInTheDocument();
        expect(screen.getByText("Groups")).toBeInTheDocument();
        expect(screen.getByText("Roles")).toBeInTheDocument();
        expect(screen.getByText("Triggers")).toBeInTheDocument();
      });
    });

    test("should close management submenu on mouse leave", async () => {
      render(<Header />, { wrapper: TestWrapper });

      const managementButton = screen.getByText("Management");
      fireEvent.mouseEnter(managementButton);

      await waitFor(() => {
        expect(screen.getByText("Users")).toBeInTheDocument();
      });

      // Find the menu list and trigger mouseLeave
      const menuItems = screen.getByText("Users").closest("ul");
      if (menuItems) {
        fireEvent.mouseLeave(menuItems);
      }

      await waitFor(() => {
        expect(screen.queryByText("Users")).not.toBeVisible();
      });
    });
  });

  describe("extended header menus", () => {
    test("should show extended menu items on hover", async () => {
      mockServerContext = {
        ...defaultServerContext,
        extendedHeaderMenus: [
          {
            name: "External Tools",
            children: [
              { name: "Tool A", url: "https://tool-a.example.com" },
              { name: "Tool B", url: "https://tool-b.example.com" },
            ],
          },
        ],
      };

      render(<Header />, { wrapper: TestWrapper });

      const extendedMenuButton = screen.getByText("External Tools");
      expect(extendedMenuButton).toBeInTheDocument();

      fireEvent.mouseEnter(extendedMenuButton);

      await waitFor(() => {
        expect(screen.getByText("Tool A")).toBeInTheDocument();
        expect(screen.getByText("Tool B")).toBeInTheDocument();
      });
    });

    test("should close extended menu on mouse leave", async () => {
      mockServerContext = {
        ...defaultServerContext,
        extendedHeaderMenus: [
          {
            name: "External Tools",
            children: [{ name: "Tool A", url: "https://tool-a.example.com" }],
          },
        ],
      };

      render(<Header />, { wrapper: TestWrapper });

      const extendedMenuButton = screen.getByText("External Tools");
      fireEvent.mouseEnter(extendedMenuButton);

      await waitFor(() => {
        expect(screen.getByText("Tool A")).toBeInTheDocument();
      });

      const menuItems = screen.getByText("Tool A").closest("ul");
      if (menuItems) {
        fireEvent.mouseLeave(menuItems);
      }

      await waitFor(() => {
        expect(screen.queryByText("Tool A")).not.toBeVisible();
      });
    });

    test("should render links with correct href in extended menu", async () => {
      mockServerContext = {
        ...defaultServerContext,
        extendedHeaderMenus: [
          {
            name: "External Tools",
            children: [{ name: "Tool A", url: "https://tool-a.example.com" }],
          },
        ],
      };

      render(<Header />, { wrapper: TestWrapper });

      fireEvent.mouseEnter(screen.getByText("External Tools"));

      await waitFor(() => {
        const toolLink = screen.getByText("Tool A");
        expect(toolLink.closest("a")).toHaveAttribute(
          "href",
          "https://tool-a.example.com",
        );
      });
    });
  });

  describe("search functionality", () => {
    test("should allow typing in search input", () => {
      render(<Header />, { wrapper: TestWrapper });

      const searchInput = screen.getByPlaceholderText("Search");
      fireEvent.change(searchInput, { target: { value: "test query" } });

      expect(searchInput).toHaveValue("test query");
    });
  });

  describe("navigation links", () => {
    test("should have link to categories", () => {
      render(<Header />, { wrapper: TestWrapper });

      const categoriesLink = screen.getByText("Categories");
      expect(categoriesLink.closest("a")).toHaveAttribute("href");
      expect(categoriesLink.closest("a")?.getAttribute("href")).toContain(
        "categories",
      );
    });

    test("should have link to entities", () => {
      render(<Header />, { wrapper: TestWrapper });

      const entitiesLink = screen.getByText("Entities");
      expect(entitiesLink.closest("a")).toHaveAttribute("href");
      expect(entitiesLink.closest("a")?.getAttribute("href")).toContain(
        "entities",
      );
    });

    test("should have link to advanced search", () => {
      render(<Header />, { wrapper: TestWrapper });

      const advancedSearchLink = screen.getByText("Advanced Search");
      expect(advancedSearchLink.closest("a")).toHaveAttribute("href");
      expect(advancedSearchLink.closest("a")?.getAttribute("href")).toContain(
        "advanced_search",
      );
    });
  });
});
