// https://github.com/dmm-com/airone/wiki/(Blueprint)-AirOne-API-Error-code-mapping
const aironeAPIErrors = {
  "AE-220000": "入力データが既存のデータと重複しています",
  "AE-122000": "入力データが大きすぎます",
};

export const GetReasonFromCode = (code: string): string => {
  return (
    aironeAPIErrors[code] ??
    `フロントエンドシステムエラー(エラーコード ${code})。 AirOne 開発者にお問合せください`
  );
};
