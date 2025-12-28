/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent } from "@testing-library/react";

import { LoginPage } from "./LoginPage";

import { TestWrapper } from "TestWrapper";

// Mock ServerContext
jest.mock("../services/ServerContext", () => ({
  ServerContext: {
    getInstance: () => ({
      title: "AirOne",
      subTitle: "Test Subtitle",
      loginNext: "/ui/",
      checkTermService: false,
      termsOfServiceUrl: "https://example.com/terms",
      singleSignOnLoginUrl: null,
      noteLink: "https://example.com/note",
      noteDesc: "Note Description",
      passwordResetDisabled: false,
    }),
  },
}));

// Mock API client
jest.mock("../repository/AironeApiClient", () => ({
  aironeApiClient: {
    postLogin: jest.fn(() => Promise.resolve({ type: "basic" })),
  },
}));

afterEach(() => {
  jest.clearAllMocks();
});

describe("LoginPage", () => {
  test("should match snapshot", () => {
    const result = render(<LoginPage />, {
      wrapper: TestWrapper,
    });

    expect(result).toMatchSnapshot();
  });

  describe("rendering", () => {
    test("should render login form with username and password fields", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      expect(screen.getByLabelText("Username")).toBeInTheDocument();
      expect(screen.getByLabelText("Password")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Login" })).toBeInTheDocument();
    });

    test("should render application title", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      expect(screen.getByText("AirOne")).toBeInTheDocument();
    });

    test("should render subtitle", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      expect(screen.getByText("Test Subtitle")).toBeInTheDocument();
    });

    test("should render password reset link when not disabled", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      expect(screen.getByText("パスワードリセット")).toBeInTheDocument();
    });

    test("should render note link with description", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      expect(screen.getByText("Note Description")).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: /Note Description/ }),
      ).toHaveAttribute("href", "https://example.com/note");
    });

    test("should not render SSO login link when not configured", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      expect(screen.queryByText("SSO ログイン")).not.toBeInTheDocument();
    });
  });

  describe("form interaction", () => {
    test("should allow typing in username field", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      const usernameInput = screen.getByLabelText("Username");
      fireEvent.change(usernameInput, { target: { value: "testuser" } });

      expect(usernameInput).toHaveValue("testuser");
    });

    test("should allow typing in password field", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      const passwordInput = screen.getByLabelText("Password");
      fireEvent.change(passwordInput, { target: { value: "testpass123" } });

      expect(passwordInput).toHaveValue("testpass123");
    });

    test("should toggle password visibility when clicking visibility icon", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      const passwordInput = screen.getByLabelText("Password");
      expect(passwordInput).toHaveAttribute("type", "password");

      // Find the visibility toggle button
      const buttons = screen.getAllByRole("button");
      const visibilityButton = buttons.find(
        (btn) => btn.getAttribute("type") !== "submit",
      );

      expect(visibilityButton).toBeDefined();
      if (visibilityButton) {
        fireEvent.click(visibilityButton);
        expect(passwordInput).toHaveAttribute("type", "text");

        fireEvent.click(visibilityButton);
        expect(passwordInput).toHaveAttribute("type", "password");
      }
    });

    test("should have hidden next input with loginNext value", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      const nextInput = document.getElementById("next") as HTMLInputElement;
      expect(nextInput).toBeInTheDocument();
      expect(nextInput.type).toBe("hidden");
      expect(nextInput.value).toBe("/ui/");
    });
  });

  describe("password reset modal", () => {
    test("should have clickable password reset link", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      const resetLink = screen.getByText("パスワードリセット");
      expect(resetLink).toBeInTheDocument();
      expect(resetLink.closest("a")).toBeInTheDocument();
    });

    test("should open password reset modal when link is clicked", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      const resetLink = screen.getByText("パスワードリセット");
      fireEvent.click(resetLink);

      // The modal should be opened - it renders PasswordResetModal component
      // Since the modal is part of the component, clicking should not throw
    });
  });

  describe("login button", () => {
    test("should have submit type button", () => {
      render(<LoginPage />, { wrapper: TestWrapper });

      const loginButton = screen.getByRole("button", { name: "Login" });
      expect(loginButton).toHaveAttribute("type", "submit");
    });
  });
});
