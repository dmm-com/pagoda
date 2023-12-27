import { ResponseError } from "@dmm-com/airone-apiclient-typescript-fetch";

import { ForbiddenError, NotFoundError, UnknownError } from "./Exceptions";

type ErrorDetail = {
  code: string;
  message: string;
};

type AironeApiNonFieldsError = {
  non_field_errors: Array<ErrorDetail>;
};

type AironeApiIndexedFieldsError = Array<ErrorDetail>;

type AironeApiFieldsError<T> = {
  [K in keyof T]?: Array<ErrorDetail>;
};

// root-level error has the same structure with ErrorDetail
export function isAironeApiRootError(jsonError: any): jsonError is ErrorDetail {
  return jsonError?.code != null && jsonError?.message != null;
}

export function isAironeApiNonFieldsError(
  jsonError: any,
): jsonError is AironeApiNonFieldsError {
  return (
    jsonError?.non_field_errors != null &&
    Array.isArray(jsonError.non_field_errors) &&
    jsonError.non_field_errors[0]?.code != null &&
    jsonError.non_field_errors[0]?.message != null
  );
}

export function isAironeApiIndexedError(
  jsonError: any,
): jsonError is AironeApiIndexedFieldsError {
  return (
    Array.isArray(jsonError) &&
    jsonError[0]?.code != null &&
    jsonError[0]?.message != null
  );
}

// https://github.com/dmm-com/airone/wiki/(Blueprint)-AirOne-API-Error-code-mapping
const aironeAPIErrors: Record<string, string> = {
  "AE-122000": "入力データが大きすぎます",
  "AE-210000": "操作に必要な権限が不足しています",
  "AE-220000": "入力データが既存のデータと重複しています",
  "AE-260000": "短期間に同じターゲットに対してインポートが発生しました",
};

const extractErrorDetail = (errorDetail: ErrorDetail): string =>
  aironeAPIErrors[errorDetail.code] ?? errorDetail.message;

export const toReportableNonFieldErrors = async (
  error: ResponseError,
): Promise<string | null> => {
  if (error.response.ok) {
    return null;
  }

  const jsonError = await error.response.json();

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

  return null;
};

// Extract error response with predefined data type, then report them appropriately
// TODO check type-safety more in runtime! currently unsafe
export const extractAPIException = async <T>(
  error: ResponseError,
  nonFieldReporter: (message: string) => void,
  fieldReporter: (name: keyof T, message: string) => void,
) => {
  if (error.response.ok) {
    return;
  }

  const jsonError = await error.response.json();

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

  const typed = jsonError as AironeApiFieldsError<T>;
  Object.keys(typed).forEach((fieldName: string) => {
    const details = (typed as Record<string, Array<ErrorDetail>>)[fieldName];
    const message = details.map((e) => extractErrorDetail(e)).join(", ");

    fieldReporter(fieldName as keyof T, message);
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
