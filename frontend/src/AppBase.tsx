import { FC, ReactNode } from "react";

import { ErrorHandler } from "ErrorHandler";
import { CheckTerms } from "components/common/CheckTerms";
import { Plugin, extractRoutes } from "plugins";
import { AppRouter } from "routes/AppRouter";
import "i18n/config";

interface Props {
  customRoutes?: {
    path: string;
    element: ReactNode;
  }[];
  plugins?: Plugin[];
}

export const AppBase: FC<Props> = ({ customRoutes, plugins = [] }) => {
  const allCustomRoutes = [...(customRoutes || []), ...extractRoutes(plugins)];

  return (
    <ErrorHandler>
      <CheckTerms>
        <AppRouter customRoutes={allCustomRoutes} />
      </CheckTerms>
    </ErrorHandler>
  );
};
