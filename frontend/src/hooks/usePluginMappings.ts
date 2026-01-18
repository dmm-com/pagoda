import { useMemo } from "react";

import { EntityPageType, EntityPluginViewsConfig } from "../plugins";
import { ServerContext } from "../services/ServerContext";

/**
 * Return type for usePluginMappings hook
 */
export interface UsePluginMappingsResult {
  config: EntityPluginViewsConfig;
  hasOverride: (entityId: number, pageType: EntityPageType) => boolean;
}

/**
 * Hook to access entity-plugin view mappings from ServerContext
 * Phase 1: Direct entityId lookup, no API calls needed
 */
export const usePluginMappings = (): UsePluginMappingsResult => {
  const serverContext = ServerContext.getInstance();
  const config = serverContext?.entityPluginViews ?? {};

  const hasOverride = useMemo(() => {
    return (entityId: number, pageType: EntityPageType): boolean => {
      const mapping = config[String(entityId)];
      if (!mapping) return false;
      return mapping.pages.includes(pageType);
    };
  }, [config]);

  return { config, hasOverride };
};
