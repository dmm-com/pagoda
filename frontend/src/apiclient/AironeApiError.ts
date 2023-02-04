export type ErrorDetail = {
  code: string;
  message: string;
};

export type AironeApiFieldsError<T> = {
  [K in keyof T]?: Array<ErrorDetail>;
};

export type AironeApiError<T> = AironeApiFieldsError<T> & {
  non_field_errors?: Array<ErrorDetail>;
};
