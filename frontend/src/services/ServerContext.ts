class User {
  id: number;
  username: string;
  isSuperuser: boolean;

  constructor(user: any) {
    this.id = user.id;
    this.username = user.username;
    this.isSuperuser = user.isSuperuser;
  }
}

const FlagKey = {
  0: "webhook",
} as const;
type FlagKey = typeof FlagKey[keyof typeof FlagKey];

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
  extendedHeaderMenus: {
    name: string;
    children: { name: string; url: string }[];
  }[];
  flags: Record<FlagKey, boolean>;

  private static _instance: ServerContext | undefined;

  constructor(context: any) {
    this.loginNext = context.next;
    this.title = context.title;
    this.subTitle = context.subtitle;
    this.noteDesc = context.note_desc;
    this.noteLink = context.note_link;
    this.version = context.version;
    this.user = context.user ? new User(context.user) : undefined;
    this.singleSignOnLoginUrl = context.singleSignOnLoginUrl;
    this.legacyUiDisabled = context.legacyUiDisabled;
    this.passwordResetDisabled = context.password_reset_disabled;
    this.checkTermService = context.checkTermService;
    this.termsOfServiceUrl = context.termsOfServiceUrl;
    this.extendedHeaderMenus = context.extendedHeaderMenus;
    this.flags = context.flags ?? { webhook: true };
  }

  static getInstance() {
    if ((window as any).django_context) {
      this._instance = new ServerContext((window as any).django_context);
    }
    return this._instance;
  }
}
