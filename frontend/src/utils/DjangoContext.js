class User {
  constructor(user) {
    this.id = user.id;
    this.isSuperuser = user.isSuperuser;
  }
}

// A JavaScript representation for Django context
export class DjangoContext {
  static #instance;

  constructor(context) {
    this.version = context.version;
    this.user = context.user ? new User(context.user) : {};
  }

  static getInstance() {
    if (window.django_context) {
      this.#instance = new DjangoContext(window.django_context);
    }
    return this.#instance;
  }
}
