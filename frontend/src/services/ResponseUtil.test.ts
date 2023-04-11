import "isomorphic-fetch";
import { ForbiddenError, NotFoundError, UnknownError } from "./Exceptions";
import { toError } from "./ResponseUtil";

test("Response should be converted to an appropriate error", () => {
  expect(toError(new Response(null, { status: 403 }))).toHaveProperty(
    "name",
    ForbiddenError.errorName
  );
  expect(toError(new Response(null, { status: 404 }))).toHaveProperty(
    "name",
    NotFoundError.errorName
  );
  expect(toError(new Response(null, { status: 599 }))).toHaveProperty(
    "name",
    UnknownError.errorName
  );
});
