export class FailedToGetEntry extends Error {
  constructor(message) {
    super(message);
    this.name = "FailedToGetEntry";
  }
}

export class FailedToGetEntity extends Error {
  constructor(message) {
    super(message);
    this.name = "FailedToGetEntity";
  }
}

export class FailedToGetUser extends Error {
  constructor(message) {
    super(message);
    this.name = "FailedToGetUser";
  }
}
