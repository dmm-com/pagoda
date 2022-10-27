export class ForbiddenError extends Error {
  static errorName = "ForbiddenError";

  constructor(message) {
    super(message);
    this.name = ForbiddenError.errorName;
  }
}
export class NotFoundError extends Error {
  static errorName = "NotFoundError";

  constructor(message) {
    super(message);
    this.name = NotFoundError.errorName;
  }
}

export class UnknownError extends Error {
  static errorName = "UnknownError";

  constructor(message) {
    super(message);
    this.name = UnknownError.errorName;
  }
}
