class User {
  id: number;
  username: string;
  isSuperuser: boolean;

  constructor(user: { id: number; username: string; isSuperuser: boolean }) {
    this.id = user.id;
    this.username = user.username;
    this.isSuperuser = user.isSuperuser;
  }
}

const FlagKey = {
  0: "webhook",
} as const;
type FlagKey = (typeof FlagKey)[keyof typeof FlagKey];

// windowオブジェクトの型拡張
declare global {
  interface Window {
    django_context?: Record<string, unknown>;
  }
}

/**
 * Context continued from server side to succeed information only server side can know.
 * Currently, it's passed via django_context in index.html.
 * ref. ~/templates/frontend/index.html
 */
export class ServerContext {
  loginNext: string;
  version: string;
  title: string;
  subTitle: string;
  noteDesc: string;
  noteLink: string;
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

  private static _instance: ServerContext | undefined;

  constructor(context: Record<string, unknown>) {
    this.loginNext = context.next as string;
    this.title = context.title as string;
    this.subTitle = context.subtitle as string;
    this.noteDesc = context.note_desc as string;
    this.noteLink = context.note_link as string;
    this.version = context.version as string;
    this.user = context.user
      ? new User(
          context.user as {
            id: number;
            username: string;
            isSuperuser: boolean;
          },
        )
      : undefined;
    this.singleSignOnLoginUrl = context.singleSignOnLoginUrl as
      | string
      | undefined;
    this.legacyUiDisabled = context.legacyUiDisabled as boolean | undefined;
    this.passwordResetDisabled = context.password_reset_disabled as
      | boolean
      | undefined;
    this.checkTermService = context.checkTermService as boolean | undefined;
    this.termsOfServiceUrl = context.termsOfServiceUrl as string | undefined;
    this.extendedGeneralParameters =
      context.extendedGeneralParameters as Record<string, unknown>;
    this.extendedHeaderMenus = context.extendedHeaderMenus as {
      name: string;
      children: { name: string; url: string }[];
    }[];
    this.headerColor = context.headerColor as string | undefined;
    this.flags = (context.flags as Record<FlagKey, boolean>) ?? {
      webhook: true,
    };
  }

  static getInstance() {
    if (typeof window !== "undefined" && window.django_context) {
      this._instance = new ServerContext(window.django_context);
    }
    return this._instance;
  }
}
