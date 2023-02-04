// https://github.com/dmm-com/airone/wiki/(Blueprint)-AirOne-API-Error-code-mapping
const aironeAPIErrors: Record<string, string> = {
  "AE-220000": "入力データが既存のデータと重複しています",
  "AE-122000": "入力データが大きすぎます",
};

export const GetReasonFromCode = (code: string): string => {
  return (
    aironeAPIErrors[code] ??
    `フロントエンドシステムエラー(エラーコード ${code})。 AirOne 開発者にお問合せください`
  );
};

export const ExtractAPIErrorMessage = (json: any): string => {
  let reasons = "";

  if (json["name"]) {
    reasons = json["name"]
      .map((errorInfo: any) =>
        GetReasonFromCode(errorInfo["airone_error_code"])
      )
      .join();
  }

  if (json["non_field_errors"]) {
    reasons = json["non_field_errors"]
      .map((errorInfo: any) =>
        GetReasonFromCode(errorInfo["airone_error_code"])
      )
      .join();
  }

  return reasons;
};
