import { FC } from "react";

import { ErrorPageBase } from "../components/common/ErrorPageBase";

export const UnavailableErrorPage: FC = () => {
  return (
    <ErrorPageBase
      title="利用できません:;(∩´﹏`∩);:"
      description={[
        "このページは現在、利用ができません。",
        "管理者からのお知らせをご覧いただくか、お問合せください。",
      ]}
    />
  );
};
