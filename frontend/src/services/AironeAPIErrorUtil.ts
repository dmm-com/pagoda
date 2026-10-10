import { ResponseError } from "@dmm-com/airone-apiclient-typescript-fetch";

import { TranslationKey, translate } from "../i18n/config";

import { ForbiddenError, NotFoundError, UnknownError } from "./Exceptions";

type ErrorDetail = {
  code: string;
  message: string;
};

type AironeApiNonFieldsError = {
  non_field_errors: Array<ErrorDetail>;
};

type AironeApiIndexedFieldsError = Array<ErrorDetail>;

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value != null && !Array.isArray(value);

const isErrorDetail = (value: unknown): value is ErrorDetail =>
  isRecord(value) &&
  typeof value.code === "string" &&
  typeof value.message === "string";

// Field-level details only need a message; the code is optional there.
type FieldErrorDetail = {
  code?: string;
  message: string;
};

const isFieldErrorDetail = (value: unknown): value is FieldErrorDetail =>
  isRecord(value) &&
  typeof value.message === "string" &&
  (value.code === undefined || typeof value.code === "string");

const isErrorDetailList = (value: unknown): value is Array<ErrorDetail> =>
  Array.isArray(value) && value.length > 0 && value.every(isErrorDetail);

// root-level error has the same structure with ErrorDetail
export function isAironeApiRootError(
  jsonError: unknown,
): jsonError is ErrorDetail {
  return isErrorDetail(jsonError);
}

export function isAironeApiNonFieldsError(
  jsonError: unknown,
): jsonError is AironeApiNonFieldsError {
  return isRecord(jsonError) && isErrorDetailList(jsonError.non_field_errors);
}

export function isAironeApiIndexedError(
  jsonError: unknown,
): jsonError is AironeApiIndexedFieldsError {
  return isErrorDetailList(jsonError);
}

// https://github.com/dmm-com/airone/wiki/(Blueprint)-AirOne-API-Error-code-mapping
const aironeAPIErrors: Record<string, TranslationKey> = {
  "AE-122000": "apiError.AE-122000",
  "AE-210000": "apiError.AE-210000",
  "AE-220000": "apiError.AE-220000",
  "AE-240000": "apiError.AE-240000",
  "AE-260000": "apiError.AE-260000",
};

const extractErrorDetail = (errorDetail: FieldErrorDetail): string => {
  const key =
    errorDetail.code != null ? aironeAPIErrors[errorDetail.code] : undefined;
  return key != null ? translate(key) : errorDetail.message;
};

export const toReportableNonFieldErrors = async (
  error: ResponseError,
): Promise<string | null> => {
  if (error.response.ok) {
    return null;
  }

  const jsonError: unknown = await error.response.json();

  if (isAironeApiRootError(jsonError)) {
    return extractErrorDetail(jsonError);
  }

  if (isAironeApiNonFieldsError(jsonError)) {
    return jsonError.non_field_errors
      .map((e) => extractErrorDetail(e))
      .join(", ");
  }

  if (isAironeApiIndexedError(jsonError)) {
    return jsonError.map((e) => extractErrorDetail(e)).join(", ");
  }

  // Field errors may be a single record or an array of records (indexed
  // nested errors); report each as "field: message".
  const fieldErrors = (Array.isArray(jsonError) ? jsonError : [jsonError])
    .filter(isRecord)
    .flatMap((item) =>
      Object.entries(item).flatMap(([field, details]) =>
        Array.isArray(details)
          ? details
              .filter(isFieldErrorDetail)
              .map((detail) => `${field}: ${extractErrorDetail(detail)}`)
          : [],
      ),
    );
  if (fieldErrors.length > 0) {
    return fieldErrors.join(", ");
  }

  return null;
};

// Extract error response with predefined data type, then report them appropriately
export const extractAPIException = async <T extends Record<string, unknown>>(
  error: ResponseError,
  nonFieldReporter: (message: string) => void,
  fieldReporter: (name: keyof T, message: string) => void,
) => {
  if (error.response.ok) {
    return;
  }

  const jsonError: unknown = await error.response.json();

  // root-level error will drop field-level errors
  if (isAironeApiRootError(jsonError)) {
    nonFieldReporter(extractErrorDetail(jsonError));
    return;
  }

  if (isAironeApiNonFieldsError(jsonError)) {
    const fullMessage = jsonError.non_field_errors
      .map((e) => extractErrorDetail(e))
      .join(", ");
    nonFieldReporter(fullMessage);
    return;
  }

  if (isAironeApiIndexedError(jsonError)) {
    const fullMessage = jsonError.map((e) => extractErrorDetail(e)).join(", ");
    nonFieldReporter(fullMessage);
    return;
  }

  if (!isRecord(jsonError)) {
    return;
  }

  Object.entries(jsonError).forEach(([fieldName, value]) => {
    const details = Array.isArray(value)
      ? value.filter(isFieldErrorDetail)
      : [];
    if (details.length > 0) {
      const message = details.map((e) => extractErrorDetail(e)).join(", ");

      // This convert snake_case to camelCase (e.g. "nw_addr" -> "nwAddr")
      const snakeToCamel = (x: string) =>
        x
          .toLowerCase()
          .replace(/(_\w)/g, (m: string) => m.toUpperCase().substr(1));

      // It's necessary to convert fieldName from snake case to cammel case because
      // server-side response its name as snake case but zod expect it as camel case.
      fieldReporter(snakeToCamel(fieldName) as keyof T, message);
    }
  });
};

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

export function isResponseError(error: Error): error is ResponseError {
  return error.name === "ResponseError";
}
