class User {
  constructor(user) {
    this.id = user.id;
    this.isSuperuser = user.isSuperuser;
  }
}

// A JavaScript representation for Django context
export class DjangoContext {
  constructor(context) {
    this.version = context.version;
    this.user = context.user ? new User(context.user) : {};

    this._instance = null;

    this.attrTypeValue = {
      string: 2,
      object: 1,
      named_object: 2049,
      array_object: 1025,
      array_string: 1026,
      array_named_object: 3073,
      array_group: 1040,
      text: 4,
      boolean: 8,
      group: 16,
      date: 32,
    };
  }

  static getInstance() {
    if (window.django_context) {
      this._instance = new DjangoContext(window.django_context);
    }
    return this._instance;
  }
}
