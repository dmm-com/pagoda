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
  }

  static getInstance() {
    if (window.django_context) {
      this._instance = new DjangoContext(window.django_context);
    }
    return this._instance;
  }
}
