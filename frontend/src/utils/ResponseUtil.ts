import { ForbiddenError, NotFoundError, UnknownError } from "./Exceptions";

export function toError(response: Response): Error | null {
  if (!response.ok) {
    switch (response.status) {
      case 403:
        return new ForbiddenError(response.toString());
      case 404:
        return new NotFoundError(response.toString());
      default:
        return new UnknownError(response.toString());
    }
  }

  return null;
}
