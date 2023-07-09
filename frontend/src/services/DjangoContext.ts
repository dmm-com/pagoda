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
  user: User | undefined;

  private static _instance: DjangoContext | undefined;

  constructor(context: any) {
    this.loginNext = context.next;
    this.title = context.title;
    this.subTitle = context.subtitle;
    this.noteDesc = context.note_desc;
    this.noteLink = context.note_link;
    this.version = context.version;
    this.user = context.user ? new User(context.user) : undefined;

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
  }

  static getInstance() {
    if ((window as any).django_context) {
      this._instance = new DjangoContext((window as any).django_context);
    }
    return this._instance;
  }
}
