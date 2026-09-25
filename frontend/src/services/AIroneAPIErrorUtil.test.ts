import { ResponseError } from "@dmm-com/airone-apiclient-typescript-fetch";

import {
  isAironeApiIndexedError,
  isAironeApiNonFieldsError,
  isAironeApiRootError,
  isResponseError,
  toError,
  toReportableNonFieldErrors,
} from "./AironeAPIErrorUtil";
import { ForbiddenError, NotFoundError, UnknownError } from "./Exceptions";

import i18n from "i18n/config";

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
