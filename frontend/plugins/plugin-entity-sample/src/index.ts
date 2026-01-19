// @airone/plugin-entity-sample - Entity View Sample Plugin
// Demonstrates entity-specific page routing for Phase 1 (entry.list only)

import React, { FC, ReactNode } from "react";
import SampleEntryListPage from "./pages/SampleEntryListPage";

// Local type definitions (matching @dmm-com/pagoda-core)
type EntityPageType = "entry.list";

interface PluginRoute {
  path: string;
  element: ReactNode;
}

interface EntityViewPlugin {
  id: string;
  name: string;
  version: string;
  routes: PluginRoute[];
  entityPages?: Partial<Record<EntityPageType, FC>>;
}

/**
 * Sample plugin that provides entity-specific entry list page
 * Phase 1: Only entry.list is supported
 */
const sampleEntityPlugin: EntityViewPlugin = {
  id: "sample",
  name: "Sample Entity View Plugin",
  version: "1.0.0",

  // No custom routes (we use entityPages instead)
  routes: [],

  // Entity-specific pages
  entityPages: {
    "entry.list": () => React.createElement(SampleEntryListPage),
  },
};

export default sampleEntityPlugin;
