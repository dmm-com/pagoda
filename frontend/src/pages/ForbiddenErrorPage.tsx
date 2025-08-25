import { FC } from "react";

import { ErrorPageBase } from "../components/common/ErrorPageBase";

export const ForbiddenErrorPage: FC = () => {
  return (
    <ErrorPageBase
      title="権限がありません… (|| ﾟДﾟ)"
      description={[
        "あなたはこのページを閲覧する権限を持っていません。",
        "ページの管理者がアクセス権を付与できる可能性があります。",
      ]}
    />
  );
};
