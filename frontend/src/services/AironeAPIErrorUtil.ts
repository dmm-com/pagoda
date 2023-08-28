import { ResponseError } from "@dmm-com/airone-apiclient-typescript-fetch";

import { ForbiddenError, NotFoundError, UnknownError } from "./Exceptions";

type ErrorDetail = {
  code: string;
  message: string;
};

type AironeApiFieldsError<T> = {
  [K in keyof T]?: Array<ErrorDetail>;
};

type AironeApiError<T> = AironeApiFieldsError<T> & {
  non_field_errors?: Array<ErrorDetail>;
};

// https://github.com/dmm-com/airone/wiki/(Blueprint)-AirOne-API-Error-code-mapping
const aironeAPIErrors: Record<string, string> = {
  "AE-220000": "入力データが既存のデータと重複しています",
  "AE-122000": "入力データが大きすぎます",
};

const extractErrorDetail = (errorDetail: ErrorDetail): string =>
  aironeAPIErrors[errorDetail.code] ?? errorDetail.message;

// Extract error response with predefined data type, then report them appropriately
// TODO check type-seafety more in runtime! currently unsafe
export const extractAPIException = async <T>(
  errpr: ResponseError,
  nonFieldReporter: (message: string) => void,
  fieldReporter: (name: keyof T, message: string) => void
) => {
  if (errpr.response.ok) {
    return;
  }

  const json = await errpr.response.json();
  const typed = json as AironeApiError<T>;

  if (typed.non_field_errors != null) {
    const fullMessage = typed.non_field_errors
      .map((e) => extractErrorDetail(e))
      .join(", ");
    nonFieldReporter(fullMessage);
  }

  Object.keys(typed as AironeApiFieldsError<T>).forEach((fieldName: string) => {
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
