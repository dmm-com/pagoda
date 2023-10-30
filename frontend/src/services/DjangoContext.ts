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

// A JavaScript representation for Django context
export class DjangoContext {
  loginNext: string;
  version: string;
  title: string;
  subTitle: string;
  noteDesc: string;
  noteLink: string;
  user?: User;
  singleSignOnLoginUrl?: string;
  legacyUiDisabled?: boolean;
  extendedHeaderMenus: {
    name: string;
    children: { name: string; url: string }[];
  }[];

  private static _instance: DjangoContext | undefined;

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
    this.extendedHeaderMenus = context.extendedHeaderMenus;
  }

  static getInstance() {
    if ((window as any).django_context) {
      this._instance = new DjangoContext((window as any).django_context);
    }
    return this._instance;
  }
}
