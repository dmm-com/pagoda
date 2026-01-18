import { FC } from "react";
import { useParams } from "react-router";

import { usePluginMappings } from "../hooks/usePluginMappings";
import { EntityPageType, Plugin, isEntityViewPlugin } from "../plugins";

interface Props {
  pageType: EntityPageType;
  defaultComponent: FC;
  pluginMap: Map<string, Plugin>;
}

/**
 * EntityAwareRoute - Conditional routing based on entity-plugin mappings
 * Phase 1: Only supports "entry.list" page type
 *
 * Renders plugin-provided component if entity has an override configured,
 * otherwise renders the default component.
 */
export const EntityAwareRoute: FC<Props> = ({
  pageType,
  defaultComponent: DefaultComponent,
  pluginMap,
}) => {
  const { entityId } = useParams<{ entityId: string }>();
  const { config } = usePluginMappings();

  // No entityId in URL - render default
  if (!entityId) {
    return <DefaultComponent />;
  }

  // O(1) lookup by entityId
  const mapping = config[entityId];

  // No mapping for this entity - render default
  if (!mapping || !mapping.pages.includes(pageType)) {
    return <DefaultComponent />;
  }

  // O(1) lookup by pluginId
  const plugin = pluginMap.get(mapping.plugin);

  if (!plugin) {
    console.warn(
      `EntityAwareRoute: Plugin "${mapping.plugin}" not found for entity ${entityId}`,
    );
    return <DefaultComponent />;
  }

  // Check if plugin supports entity pages
  if (!isEntityViewPlugin(plugin)) {
    console.warn(
      `EntityAwareRoute: Plugin "${mapping.plugin}" does not support entity pages`,
    );
    return <DefaultComponent />;
  }

  // Get the component for this page type
  const PluginComponent = plugin.entityPages?.[pageType];

  if (!PluginComponent) {
    console.warn(
      `EntityAwareRoute: Plugin "${mapping.plugin}" does not provide "${pageType}" page`,
    );
    return <DefaultComponent />;
  }

  return <PluginComponent />;
};
