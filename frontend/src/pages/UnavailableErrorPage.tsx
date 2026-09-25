import { FC } from "react";

import { ErrorPageBase } from "../components/common/ErrorPageBase";
import { useTranslation } from "../hooks/useTranslation";

export const UnavailableErrorPage: FC = () => {
  const { t } = useTranslation();
  return (
    <ErrorPageBase
      title={t("errorPage.unavailable.title")}
      description={[
        t("errorPage.unavailable.description1"),
        t("errorPage.unavailable.description2"),
      ]}
    />
  );
};
