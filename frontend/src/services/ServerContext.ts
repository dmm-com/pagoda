import { z } from "zod";

import {
  EntityPageType,
  FrontendPluginEntityOverridesConfig,
} from "../plugins";

export class User {
  id: number;
  username: string;
  isSuperuser: boolean;
  isReadonly: boolean;
  parentUser: number | null;
  email: string;

  constructor(user: {
    id: number;
    username: string;
    isSuperuser: boolean;
    isReadonly: boolean;
    parentUser: number | null;
    email: string;
  }) {
    this.id = user.id;
    this.username = user.username;
    this.isSuperuser = user.isSuperuser;
    this.isReadonly = user.isReadonly;
    this.parentUser = user.parentUser;
    this.email = user.email;
  }
}

const FlagKey = {
  0: "webhook",
} as const;
type FlagKey = (typeof FlagKey)[keyof typeof FlagKey];

// Type extension for the window object
declare global {
  interface Window {
    django_context?: Record<string, unknown>;
  }
}

/**
 * Fall back to `fallback` when a field is malformed, so that a single bad
 * server-side setting does not break the whole UI.
 */
const withFallback = <T extends z.ZodTypeAny>(
  key: string,
  schema: T,
  fallback: z.infer<T>,
) =>
  schema.catch(({ error }: { error: z.ZodError }) => {
    console.warn(`Invalid django_context.${key}; using fallback`, error);
    return fallback;
  });

const optionalString = (key: string) =>
  withFallback(key, z.string().optional(), undefined);
const optionalBoolean = (key: string) =>
  withFallback(key, z.boolean().optional(), undefined);

// The login page (templates/registration/login.html) and the main app
// (templates/frontend/index.html) provide different subsets of these fields.
const djangoContextSchema = z.object({
  next: optionalString("next"),
  title: optionalString("title"),
  subtitle: optionalString("subtitle"),
  note_desc: optionalString("note_desc"),
  note_link: optionalString("note_link"),
  version: optionalString("version"),
  user: withFallback(
    "user",
    z
      .object({
        id: z.number(),
        username: z.string(),
        isSuperuser: z.boolean(),
        isReadonly: z.boolean(),
        parentUser: z.number().nullable(),
        email: z.string(),
      })
      .optional(),
    undefined,
  ),
  singleSignOnLoginUrl: optionalString("singleSignOnLoginUrl"),
  legacyUiDisabled: optionalBoolean("legacyUiDisabled"),
  password_reset_disabled: optionalBoolean("password_reset_disabled"),
  checkTermService: optionalBoolean("checkTermService"),
  termsOfServiceUrl: optionalString("termsOfServiceUrl"),
  extendedGeneralParameters: withFallback(
    "extendedGeneralParameters",
    z.record(z.unknown()).default({}),
    {},
  ),
  extendedHeaderMenus: withFallback(
    "extendedHeaderMenus",
    z
      .array(
        z.object({
          name: z.string(),
          children: z.array(z.object({ name: z.string(), url: z.string() })),
        }),
      )
      .default([]),
    [],
  ),
  headerColor: withFallback(
    "headerColor",
    z.string().nullable().optional(),
    undefined,
  ),
  flags: withFallback(
    "flags",
    z.object({ webhook: z.boolean() }).default({ webhook: true }),
    { webhook: true },
  ),
  frontendPluginEntityOverrides: withFallback(
    "frontendPluginEntityOverrides",
    z
      .record(
        z.object({
          plugin: z.string(),
          // Ignore page types this frontend does not know about
          pages: z
            .array(z.string())
            .transform((pages) =>
              pages.filter(
                (page): page is EntityPageType => page === "entry.list",
              ),
            ),
        }),
      )
      .default({}),
    {},
  ),
});

/**
 * Context continued from server side to succeed information only server side can know.
 * Currently, it's passed via django_context in index.html.
 * ref. ~/templates/frontend/index.html
 */
export class ServerContext {
  loginNext?: string;
  version?: string;
  title?: string;
  subTitle?: string;
  noteDesc?: string;
  noteLink?: string;
  user?: User;
  singleSignOnLoginUrl?: string;
  legacyUiDisabled?: boolean;
  passwordResetDisabled?: boolean;
  checkTermService?: boolean;
  termsOfServiceUrl?: string;
  extendedGeneralParameters: Record<string, unknown>;
  extendedHeaderMenus: {
    name: string;
    children: { name: string; url: string }[];
  }[];
  headerColor?: string;
  flags: Record<FlagKey, boolean>;
  frontendPluginEntityOverrides: FrontendPluginEntityOverridesConfig;

  private static _instance: ServerContext | undefined;
  private static _source: Record<string, unknown> | undefined;

  constructor(context: Record<string, unknown>) {
    const parsed = djangoContextSchema.parse(context);

    this.loginNext = parsed.next;
    this.title = parsed.title;
    this.subTitle = parsed.subtitle;
    this.noteDesc = parsed.note_desc;
    this.noteLink = parsed.note_link;
    this.version = parsed.version;
    this.user = parsed.user != null ? new User(parsed.user) : undefined;
    this.singleSignOnLoginUrl = parsed.singleSignOnLoginUrl;
    this.legacyUiDisabled = parsed.legacyUiDisabled;
    this.passwordResetDisabled = parsed.password_reset_disabled;
    this.checkTermService = parsed.checkTermService;
    this.termsOfServiceUrl = parsed.termsOfServiceUrl;
    this.extendedGeneralParameters = parsed.extendedGeneralParameters;
    this.extendedHeaderMenus = parsed.extendedHeaderMenus;
    this.headerColor = parsed.headerColor ?? undefined;
    this.flags = parsed.flags;
    this.frontendPluginEntityOverrides = parsed.frontendPluginEntityOverrides;
  }

  static getInstance() {
    // Re-parse only when the source object changes; getInstance() is called
    // on every render by some components.
    if (
      typeof window !== "undefined" &&
      window.django_context &&
      window.django_context !== this._source
    ) {
      this._instance = new ServerContext(window.django_context);
      this._source = window.django_context;
    }
    return this._instance;
  }
}
