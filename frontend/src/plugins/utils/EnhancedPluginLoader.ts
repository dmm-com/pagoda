import type { Plugin } from '../types';

/**
 * Enhanced Plugin Loader
 * 
 * Supports both local plugins (frontend/packages) and external npm modules
 * Automatically discovers plugins using multiple strategies:
 * 1. Local plugins: frontend/packages/*/src/index.ts
 * 2. External npm plugins: node_modules/airone-plugin-*/index.js
 * 3. Scoped npm plugins: node_modules/@*/airone-plugin-*/index.js
 */
export class EnhancedPluginLoader {
  private static instance: EnhancedPluginLoader | null = null;
  private plugins: Plugin[] = [];
  private loaded = false;

  private constructor() {}

  static getInstance(): EnhancedPluginLoader {
    if (!EnhancedPluginLoader.instance) {
      EnhancedPluginLoader.instance = new EnhancedPluginLoader();
    }
    return EnhancedPluginLoader.instance;
  }

  /**
   * Load plugins from multiple sources
   */
  async loadPlugins(): Promise<Plugin[]> {
    if (this.loaded) {
      return this.plugins;
    }

    try {
      console.log('[EnhancedPluginLoader] Starting comprehensive plugin discovery...');
      
      // Load plugins from multiple sources in parallel
      const [localPlugins, npmPlugins, scopedPlugins] = await Promise.all([
        this.loadLocalPlugins(),
        this.loadNpmPlugins(), 
        this.loadScopedNpmPlugins()
      ]);

      // Combine and deduplicate plugins
      const allPlugins = [...localPlugins, ...npmPlugins, ...scopedPlugins];
      const uniquePlugins = this.deduplicatePlugins(allPlugins);

      // Sort plugins by priority (higher priority first)
      uniquePlugins.sort((a, b) => {
        const priorityA = a.priority || 0;
        const priorityB = b.priority || 0;
        return priorityB - priorityA;
      });

      console.log(`[EnhancedPluginLoader] Successfully loaded ${uniquePlugins.length} unique plugins:`, 
        uniquePlugins.map(p => ({ 
          id: p.id, 
          name: p.name, 
          version: p.version, 
          priority: p.priority,
          source: this.getPluginSource(p)
        }))
      );

      this.plugins = uniquePlugins;
      this.loaded = true;
      
      return this.plugins;
    } catch (error) {
      console.error('[EnhancedPluginLoader] Failed to load plugins:', error);
      return [];
    }
  }

  /**
   * Load local plugins from frontend/packages/
   */
  private loadLocalPlugins(): Plugin[] {
    const plugins: Plugin[] = [];
    
    try {
      // Use require.context for local plugins
      const localContext = (require as any).context( // eslint-disable-line @typescript-eslint/no-explicit-any
        '../../../packages',
        true,
        /^\.\/[^\/]+\/src\/index\.ts$/
      );

      localContext.keys().forEach((pluginPath: string) => {
        try {
          console.log(`[EnhancedPluginLoader] Loading local plugin: ${pluginPath}`);
          const pluginModule = localContext(pluginPath);
          const plugin = pluginModule.default || pluginModule;
          
          if (this.isValidPlugin(plugin)) {
            plugin._source = 'local'; // Mark source
            plugins.push(plugin as Plugin);
          }
        } catch (error) {
          console.error(`[EnhancedPluginLoader] Failed to load local plugin ${pluginPath}:`, error);
        }
      });
    } catch (error) {
      console.warn('[EnhancedPluginLoader] Local plugins not available:', error);
    }

    return plugins;
  }

  /**
   * Load npm plugins matching pattern: airone-plugin-*
   */
  private loadNpmPlugins(): Plugin[] {
    const plugins: Plugin[] = [];
    
    try {
      // Use require.context for npm plugins
      const npmContext = (require as any).context( // eslint-disable-line @typescript-eslint/no-explicit-any
        '../../../node_modules',
        true,
        /^\.\/airone-plugin-[^\/]+\/index\.(js|ts)$/
      );

      npmContext.keys().forEach((pluginPath: string) => {
        try {
          console.log(`[EnhancedPluginLoader] Loading npm plugin: ${pluginPath}`);
          const pluginModule = npmContext(pluginPath);
          const plugin = pluginModule.default || pluginModule;
          
          if (this.isValidPlugin(plugin)) {
            plugin._source = 'npm'; // Mark source
            plugins.push(plugin as Plugin);
          }
        } catch (error) {
          console.error(`[EnhancedPluginLoader] Failed to load npm plugin ${pluginPath}:`, error);
        }
      });
    } catch (error) {
      console.warn('[EnhancedPluginLoader] NPM plugins not available:', error);
    }

    return plugins;
  }

  /**
   * Load scoped npm plugins matching pattern: @scope/airone-plugin-*
   */
  private loadScopedNpmPlugins(): Plugin[] {
    const plugins: Plugin[] = [];
    
    try {
      // Use require.context for scoped npm plugins
      const scopedContext = (require as any).context( // eslint-disable-line @typescript-eslint/no-explicit-any
        '../../../node_modules',
        true,
        /^\.\/\@[^\/]+\/airone-plugin-[^\/]+\/index\.(js|ts)$/
      );

      scopedContext.keys().forEach((pluginPath: string) => {
        try {
          console.log(`[EnhancedPluginLoader] Loading scoped npm plugin: ${pluginPath}`);
          const pluginModule = scopedContext(pluginPath);
          const plugin = pluginModule.default || pluginModule;
          
          if (this.isValidPlugin(plugin)) {
            plugin._source = 'scoped-npm'; // Mark source
            plugins.push(plugin as Plugin);
          }
        } catch (error) {
          console.error(`[EnhancedPluginLoader] Failed to load scoped npm plugin ${pluginPath}:`, error);
        }
      });
    } catch (error) {
      console.warn('[EnhancedPluginLoader] Scoped NPM plugins not available:', error);
    }

    return plugins;
  }

  /**
   * Validate plugin structure
   */
  private isValidPlugin(plugin: any): boolean { // eslint-disable-line @typescript-eslint/no-explicit-any
    return plugin && 
           typeof plugin === 'object' && 
           plugin.id && 
           typeof plugin.id === 'string' &&
           plugin.name &&
           typeof plugin.name === 'string';
  }

  /**
   * Remove duplicate plugins based on ID
   */
  private deduplicatePlugins(plugins: Plugin[]): Plugin[] {
    const seen = new Set<string>();
    return plugins.filter(plugin => {
      if (seen.has(plugin.id)) {
        console.warn(`[EnhancedPluginLoader] Duplicate plugin ID detected: ${plugin.id} - skipping`);
        return false;
      }
      seen.add(plugin.id);
      return true;
    });
  }

  /**
   * Get plugin source type
   */
  private getPluginSource(plugin: any): string { // eslint-disable-line @typescript-eslint/no-explicit-any
    return plugin._source || 'unknown';
  }

  /**
   * Get all loaded plugins
   */
  getPlugins(): Plugin[] {
    return this.plugins;
  }

  /**
   * Get plugin by ID
   */
  getPlugin(id: string): Plugin | undefined {
    return this.plugins.find(p => p.id === id);
  }

  /**
   * Reset loader state (mainly for testing)
   */
  reset(): void {
    this.plugins = [];
    this.loaded = false;
  }
}

/**
 * Convenience function to load all plugins (enhanced version)
 */
export async function loadAllPluginsEnhanced(): Promise<Plugin[]> {
  const loader = EnhancedPluginLoader.getInstance();
  return await loader.loadPlugins();
}

/**
 * Get all loaded plugins (enhanced version)
 */
export function getLoadedPluginsEnhanced(): Plugin[] {
  const loader = EnhancedPluginLoader.getInstance();
  return loader.getPlugins();
}