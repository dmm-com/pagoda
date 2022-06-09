export class FailedToGetEntry extends Error {
  constructor(message) {
    super(message);
    this.name = "FailedToGetEntry";
  }
}
