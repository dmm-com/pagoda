import React, { FC } from "react";

import { ErrorHandler } from "ErrorHandler";
import { CheckTerms } from "components/common/CheckTerms";
import { AppRouter } from "routes/AppRouter";
import "i18n/config";

interface Props {
  customRoutes?: {
    path: string;
    element: React.ReactNode;
  }[];
}

export const AppBase: FC<Props> = ({ customRoutes }) => {
  return (
    <ErrorHandler>
      <CheckTerms>
        <AppRouter customRoutes={customRoutes} />
      </CheckTerms>
    </ErrorHandler>
  );
};
