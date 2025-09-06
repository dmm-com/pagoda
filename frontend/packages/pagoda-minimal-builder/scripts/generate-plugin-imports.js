#!/usr/bin/env node

/**
 * Plugin Import Generator
 *
 * Automatically generates plugin import statements based on
 * plugins.config.js content. This enables static plugin resolution at build time.
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import pluginsConfig from "../plugins.config.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Generate file content
const generateContent = () => {
  const imports = [];
  const pluginVariables = [];

  // Generate import statement for each plugin
  pluginsConfig.plugins.forEach((pluginName, index) => {
    const varName = `plugin${index}`;
    imports.push(`import ${varName} from "${pluginName}";`);
    pluginVariables.push(varName);
  });

  // Generate file content
  return `// This file is auto-generated. Do not edit directly.
// Edit plugins.config.js and run npm run build instead.

${imports.join("\n")}

// Export all plugins
export const configuredPlugins = [
  ${pluginVariables.join(",\n  ")}
].filter(Boolean);

console.log('[Generated Plugin Imports] Configured plugins:', configuredPlugins.map(p => p.id));
`;
};

// Generate file
const outputPath = path.join(__dirname, "..", "src", "generatedPlugins.ts");
const content = generateContent();

fs.writeFileSync(outputPath, content, "utf-8");
console.log(`✅ Generated plugin imports at: ${outputPath}`);
console.log(`   Included plugins: ${pluginsConfig.plugins.join(", ")}`);
