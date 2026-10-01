import { FC } from "react";

import { ErrorPageBase } from "../components/common/ErrorPageBase";
import { useTranslation } from "../hooks/useTranslation";

export const ForbiddenErrorPage: FC = () => {
  const { t } = useTranslation();
  return (
    <ErrorPageBase
      title={t("errorPage.forbidden.title")}
      description={[
        t("errorPage.forbidden.description1"),
        t("errorPage.forbidden.description2"),
      ]}
    />
  );
};
