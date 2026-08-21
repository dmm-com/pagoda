import fs from "node:fs";
import path from "node:path";

import type { Plugin } from "vite";

/**
 * Mirror webpack/jest `resolve.modules: [frontend/src, node_modules]`.
 * Vite does not honor tsconfig `baseUrl` for bare imports such as `TestWrapper`.
 */
export function frontendSrcResolver(frontendSrc: string): Plugin {
  const suffixes = [".tsx", ".ts", ".jsx", ".js", ""];

  return {
    name: "frontend-src-resolver",
    enforce: "pre",
    resolveId(source) {
      if (
        !source ||
        source.startsWith(".") ||
        source.startsWith("\0") ||
        path.isAbsolute(source)
      ) {
        return null;
      }
      // Scoped packages resolve via node_modules (or explicit aliases).
      if (source.startsWith("@")) {
        return null;
      }

      for (const suffix of suffixes) {
        const candidate = path.join(frontendSrc, `${source}${suffix}`);
        if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
          return candidate;
        }
      }

      for (const suffix of suffixes) {
        const candidate = path.join(frontendSrc, source, `index${suffix}`);
        if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
          return candidate;
        }
      }

      return null;
    },
  };
}
