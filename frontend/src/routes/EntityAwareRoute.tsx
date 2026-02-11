import { Box, CircularProgress } from "@mui/material";
import { FC, useMemo } from "react";
import { useParams } from "react-router";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { usePluginMappings } from "../hooks/usePluginMappings";
import { SchemaValidationErrorPage } from "../pages/SchemaValidationErrorPage";
import { EntityPageType, Plugin, isEntityViewPlugin } from "../plugins";
import { toAttrRecord } from "../plugins/schema";
import { aironeApiClient } from "../repository/AironeApiClient";

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
 *
 * When a plugin defines an attrSchema, this component will:
 * 1. Fetch the entity details
 * 2. Convert attrs to AttrRecord format
 * 3. Validate using Zod's safeParse
 * 4. Show an error page if validation fails
 */
export const EntityAwareRoute: FC<Props> = ({
  pageType,
  defaultComponent: DefaultComponent,
  pluginMap,
}) => {
  const { entityId } = useParams<{ entityId: string }>();
  const { config } = usePluginMappings();

  // Determine if we need to fetch entity and the target plugin
  const { shouldFetchEntity, plugin, mapping } = useMemo(() => {
    if (!entityId) {
      return { shouldFetchEntity: false, plugin: null, mapping: null };
    }

    const mapping = config[entityId];
    if (!mapping || !mapping.pages.includes(pageType)) {
      return { shouldFetchEntity: false, plugin: null, mapping: null };
    }

    const plugin = pluginMap.get(mapping.plugin);

    if (!plugin || !isEntityViewPlugin(plugin)) {
      return { shouldFetchEntity: false, plugin: null, mapping };
    }

    // Only fetch entity if plugin has an attrSchema
    const shouldFetchEntity = !!plugin.attrSchema;
    return { shouldFetchEntity, plugin, mapping };
  }, [entityId, config, pageType, pluginMap]);

  // Fetch entity for schema validation (only when needed)
  const entityState = useAsyncWithThrow(async () => {
    if (!shouldFetchEntity || !entityId) {
      return null;
    }
    return await aironeApiClient.getEntity(Number(entityId));
  }, [shouldFetchEntity, entityId]);

  // Validate entity against plugin schema
  const validationResult = useMemo(() => {
    if (!plugin || !isEntityViewPlugin(plugin) || !plugin.attrSchema) {
      return { success: true as const, errors: [] };
    }

    if (!entityState.value) {
      // Still loading or no entity to validate
      return { success: true as const, errors: [] };
    }

    // Convert to AttrRecord and validate with Zod's safeParse
    const attrRecord = toAttrRecord(entityState.value);
    const result = plugin.attrSchema.safeParse(attrRecord);

    return result.success
      ? { success: true as const, errors: [] }
      : { success: false as const, errors: result.error.issues };
  }, [plugin, entityState.value]);

  // No entityId in URL - render default
  if (!entityId) {
    return <DefaultComponent />;
  }

  // No mapping for this entity - render default
  if (!mapping || !mapping.pages.includes(pageType)) {
    return <DefaultComponent />;
  }

  // Plugin not found - render default with warning
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

  // If plugin has schema, wait for entity to load
  if (plugin.attrSchema && entityState.loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="200px"
      >
        <CircularProgress />
      </Box>
    );
  }

  // Schema validation failed - show error page
  if (!validationResult.success) {
    return (
      <SchemaValidationErrorPage
        entityName={entityState.value?.name}
        pluginName={plugin.name}
        errors={validationResult.errors}
      />
    );
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
