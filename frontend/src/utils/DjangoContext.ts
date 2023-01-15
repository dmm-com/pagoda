class User {
  id: number;
  isSuperuser: boolean;

  constructor(user: any) {
    this.id = user.id;
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
  attrTypeValue: any;
  aclObjectType: {
    [name: string]: number;
  };
  aclTypes: {
    [name: string]: { value: number; name: string };
  };
  user: User | undefined;
  userAuthenticateType: {
    [name: string]: number;
  };

  private static _instance: DjangoContext | undefined;

  constructor(context: any) {
    this.loginNext = context.next;
    this.title = context.title;
    this.subTitle = context.subtitle;
    this.noteDesc = context.note_desc;
    this.noteLink = context.note_link;
    this.version = context.version;
    this.user = context.user ? new User(context.user) : undefined;

    this.userAuthenticateType = {
      local: 1 << 0,
      ldap: 1 << 1,
    };

    this.attrTypeValue = {
      string: 2,
      object: 1,
      named_object: 2049,
      array_object: 1025,
      array_string: 1026,
      array_named_object: 3073,
      array_named_object_boolean: 3081,
      array_group: 1040,
      array_role: 1088,
      text: 4,
      boolean: 8,
      group: 16,
      date: 32,
      role: 64,
    };

    this.aclTypes = {
      nothing: { value: 1, name: "権限なし" },
      readable: { value: 2, name: "閲覧" },
      writable: { value: 4, name: "閲覧・編集" },
      full: { value: 8, name: "閲覧・編集・削除" },
    };

    this.aclObjectType = {
      entity: 1 << 0,
      entityAttr: 1 << 1,
      entry: 1 << 2,
      entryAttr: 1 << 3,
    };
  }

  static getInstance() {
    if ((window as any).django_context) {
      this._instance = new DjangoContext((window as any).django_context);
    }
    return this._instance;
  }
}
