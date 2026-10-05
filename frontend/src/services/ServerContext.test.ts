import { ServerContext } from "./ServerContext";

describe("ServerContext", () => {
  beforeEach(() => {
    vi.spyOn(console, "warn").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("should parse the main app context", () => {
    const context = new ServerContext({
      version: "v1.0",
      title: "Pagoda",
      user: {
        id: 1,
        username: "admin",
        isSuperuser: true,
        isReadonly: false,
        parentUser: null,
        email: "admin@example.com",
      },
      legacyUiDisabled: false,
      checkTermService: false,
      extendedGeneralParameters: { key: "value" },
      extendedHeaderMenus: [
        { name: "Links", children: [{ name: "a", url: "https://a.test" }] },
      ],
      headerColor: null,
      flags: { webhook: false },
      frontendPluginEntityOverrides: {
        "10": { plugin: "sample", pages: ["entry.list"] },
      },
    });

    expect(context.version).toBe("v1.0");
    expect(context.user?.id).toBe(1);
    expect(context.user?.parentUser).toBeNull();
    expect(context.extendedGeneralParameters).toEqual({ key: "value" });
    expect(context.extendedHeaderMenus).toHaveLength(1);
    expect(context.headerColor).toBeUndefined();
    expect(context.flags).toEqual({ webhook: false });
    expect(context.frontendPluginEntityOverrides).toEqual({
      "10": { plugin: "sample", pages: ["entry.list"] },
    });
    expect(console.warn).not.toHaveBeenCalled();
  });

  test("should parse the login page context with defaults", () => {
    const context = new ServerContext({
      next: "/ui/",
      title: "Pagoda",
      subtitle: "sub",
      note_desc: "desc",
      note_link: "https://note.test",
      termsOfServiceUrl: "#",
      password_reset_disabled: true,
      checkTermService: false,
    });

    expect(context.loginNext).toBe("/ui/");
    expect(context.subTitle).toBe("sub");
    expect(context.passwordResetDisabled).toBe(true);
    expect(context.user).toBeUndefined();
    expect(context.extendedGeneralParameters).toEqual({});
    expect(context.extendedHeaderMenus).toEqual([]);
    expect(context.flags).toEqual({ webhook: true });
    expect(context.frontendPluginEntityOverrides).toEqual({});
    expect(console.warn).not.toHaveBeenCalled();
  });

  test("should fall back per field on malformed values", () => {
    const context = new ServerContext({
      title: "Pagoda",
      extendedHeaderMenus: [{ name: "Links" }],
      flags: "invalid",
    });

    expect(context.title).toBe("Pagoda");
    expect(context.extendedHeaderMenus).toEqual([]);
    expect(context.flags).toEqual({ webhook: true });
    expect(console.warn).toHaveBeenCalledTimes(2);
  });

  test("should ignore unknown plugin page types", () => {
    const context = new ServerContext({
      frontendPluginEntityOverrides: {
        "10": { plugin: "sample", pages: ["entry.list", "entry.unknown"] },
      },
    });

    expect(context.frontendPluginEntityOverrides).toEqual({
      "10": { plugin: "sample", pages: ["entry.list"] },
    });
  });
});
