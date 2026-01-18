import { FC, ReactNode, useMemo } from "react";

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

  // Convert plugins array to Map for O(1) lookup
  const pluginMap = useMemo(
    () => new Map(plugins.map((p) => [p.id, p])),
    [plugins],
  );

  return (
    <ErrorHandler>
      <CheckTerms>
        <AppRouter customRoutes={allCustomRoutes} pluginMap={pluginMap} />
      </CheckTerms>
    </ErrorHandler>
  );
};
