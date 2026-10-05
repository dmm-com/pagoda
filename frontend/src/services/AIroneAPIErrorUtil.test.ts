import { ResponseError } from "@dmm-com/airone-apiclient-typescript-fetch";

import {
  extractAPIException,
  isAironeApiIndexedError,
  isAironeApiNonFieldsError,
  isAironeApiRootError,
  isResponseError,
  toError,
  toReportableNonFieldErrors,
} from "./AironeAPIErrorUtil";
import { ForbiddenError, NotFoundError, UnknownError } from "./Exceptions";

import i18n from "i18n/config";

const responseErrorOf = (body: unknown): ResponseError =>
  new ResponseError(new Response(JSON.stringify(body), { status: 400 }));

test("type guards should reject malformed details", () => {
  expect(isAironeApiRootError(null)).toBeFalsy();
  expect(isAironeApiRootError({ code: 1, message: "dummy" })).toBeFalsy();
  expect(isAironeApiNonFieldsError({ non_field_errors: [] })).toBeFalsy();
  expect(isAironeApiIndexedError([])).toBeFalsy();
  expect(
    isAironeApiIndexedError([
      { code: "AE-000000", message: "dummy" },
      { code: "AE-000000" },
    ]),
  ).toBeFalsy();
});

test("toReportableNonFieldErrors should report each error shape", async () => {
  expect(
    await toReportableNonFieldErrors(
      responseErrorOf({ code: "AE-210000", message: "raw" }),
    ),
  ).toBe("操作に必要な権限が不足しています");
  expect(
    await toReportableNonFieldErrors(
      responseErrorOf({
        non_field_errors: [
          { code: "AE-000000", message: "a" },
          { code: "AE-000000", message: "b" },
        ],
      }),
    ),
  ).toBe("a, b");
  expect(
    await toReportableNonFieldErrors(
      responseErrorOf([{ code: "AE-000000", message: "indexed" }]),
    ),
  ).toBe("indexed");
  // field-level details without a code are still reported
  expect(
    await toReportableNonFieldErrors(
      responseErrorOf({ name: [{ message: "field" }], other: "ignored" }),
    ),
  ).toBe("name: field");
  expect(await toReportableNonFieldErrors(responseErrorOf("text"))).toBeNull();
});

test("extractAPIException should report field errors in camelCase", async () => {
  const nonFieldReporter = vi.fn();
  const fieldReporter = vi.fn();

  await extractAPIException<{ nwAddr: string }>(
    responseErrorOf({
      nw_addr: [{ code: "AE-121000", message: "invalid" }],
      broken: "not-a-list",
    }),
    nonFieldReporter,
    fieldReporter,
  );

  expect(nonFieldReporter).not.toHaveBeenCalled();
  expect(fieldReporter).toHaveBeenCalledTimes(1);
  expect(fieldReporter).toHaveBeenCalledWith("nwAddr", "invalid");
});

test("isAironeApiRootError should recognize an error is a root-level(same as ErrorDetail) or not", () => {
  expect(
    isAironeApiRootError({ code: "AE-000000", message: "dummy" }),
  ).toBeTruthy();

  expect(isAironeApiRootError({ field: "others" })).toBeFalsy();
  expect(
    isAironeApiRootError({
      non_field_errors: [{ code: "AE-000000", message: "dummy" }],
    }),
  ).toBeFalsy(); // non-field error
  expect(
    isAironeApiRootError([{ code: "AE-000000", message: "dummy" }]),
  ).toBeFalsy(); // indexed error
});

test("isAironeApiNonFieldsError should recognize an error is a non-field or not", () => {
  expect(
    isAironeApiNonFieldsError({
      non_field_errors: [{ code: "AE-000000", message: "dummy" }],
    }),
  ).toBeTruthy();

  expect(isAironeApiNonFieldsError({ field: "others" })).toBeFalsy();
  expect(
    isAironeApiNonFieldsError({ code: "AE-000000", message: "dummy" }),
  ).toBeFalsy(); // root-level error
  expect(
    isAironeApiNonFieldsError([{ code: "AE-000000", message: "dummy" }]),
  ).toBeFalsy(); // indexed error
});

test("isAironeApiIndexedError should recognize an error is a indexed(array) errors or not", () => {
  expect(
    isAironeApiIndexedError([{ code: "AE-000000", message: "dummy" }]),
  ).toBeTruthy();

  expect(isAironeApiIndexedError({ field: "others" })).toBeFalsy();
  expect(
    isAironeApiIndexedError({ code: "AE-000000", message: "dummy" }),
  ).toBeFalsy(); // root-level error
  expect(
    isAironeApiIndexedError({
      non_field_errors: [{ code: "AE-000000", message: "dummy" }],
    }),
  ).toBeFalsy(); // non-field error
});

test("Response should be converted to an appropriate error", () => {
  expect(toError(new Response(null, { status: 403 }))).toHaveProperty(
    "name",
    ForbiddenError.errorName,
  );
  expect(toError(new Response(null, { status: 404 }))).toHaveProperty(
    "name",
    NotFoundError.errorName,
  );
  expect(toError(new Response(null, { status: 599 }))).toHaveProperty(
    "name",
    UnknownError.errorName,
  );
});

test("isResponseError should recognize an error is a ResponseError or not", () => {
  expect(isResponseError(new ResponseError(new Response()))).toBeTruthy();

  expect(isResponseError(new Error("others"))).toBeFalsy();
});

test("reports nested indexed field errors from an API error", async () => {
  const response = new Response(
    JSON.stringify([
      {
        username: [{ message: "This field is required.", code: "AE-113000" }],
        groups: [{ message: "Not a valid string.", code: "AE-121000" }],
      },
    ]),
    { status: 400, headers: { "Content-Type": "application/json" } },
  );

  await expect(
    toReportableNonFieldErrors(new ResponseError(response)),
  ).resolves.toBe(
    "username: This field is required., groups: Not a valid string.",
  );
});

describe("toReportableNonFieldErrors", () => {
  afterEach(async () => {
    await i18n.changeLanguage("ja");
  });

  test("translates a known error code to Japanese", async () => {
    const response = new Response(
      JSON.stringify({ code: "AE-210000", message: "dummy" }),
      { status: 400 },
    );
    const error = new ResponseError(response);

    expect(await toReportableNonFieldErrors(error)).toBe(
      "操作に必要な権限が不足しています",
    );
  });

  test("translates a known error code to English", async () => {
    await i18n.changeLanguage("en");

    const response = new Response(
      JSON.stringify({ code: "AE-210000", message: "dummy" }),
      { status: 400 },
    );
    const error = new ResponseError(response);

    expect(await toReportableNonFieldErrors(error)).toBe(
      "You do not have permission for this operation",
    );
  });
});
