import fs from "node:fs";
import path from "node:path";

import { createCoverageMap } from "istanbul-lib-coverage";

const thresholds: Record<
  string,
  { statements: number; branches: number; functions: number; lines: number }
> = {
  "frontend/src/components/entity/entityForm/ChoicesEditor.tsx": {
    statements: 95,
    branches: 70,
    functions: 95,
    lines: 95,
  },
  "frontend/src/components/entity/entityForm/IsolationRulesFields.tsx": {
    statements: 85,
    branches: 85,
    functions: 75,
    lines: 85,
  },
  "frontend/src/components/entry/AttrStatsModal.tsx": {
    statements: 95,
    branches: 70,
    functions: 95,
    lines: 95,
  },
  "frontend/src/components/entry/entryForm/ReferralsAutocomplete.tsx": {
    statements: 95,
    branches: 85,
    functions: 95,
    lines: 95,
  },
  "frontend/src/components/entry/entryForm/SelectAttributeValueField.tsx": {
    statements: 95,
    branches: 70,
    functions: 95,
    lines: 95,
  },
  "frontend/src/hooks/useAsync.ts": {
    statements: 100,
    branches: 100,
    functions: 100,
    lines: 100,
  },
};

export function checkFrontendCoverageThresholds(rootDir: string): Error | undefined {
  const coveragePath = path.resolve(rootDir, "coverage/coverage-final.json");
  if (!fs.existsSync(coveragePath)) {
    return undefined;
  }

  const coverageMap = createCoverageMap(JSON.parse(fs.readFileSync(coveragePath, "utf8")));
  const failures: string[] = [];

  for (const [filename, expected] of Object.entries(thresholds)) {
    const absolutePath = path.resolve(rootDir, filename);
    if (!coverageMap.data[absolutePath]) {
      failures.push(`${filename}: no coverage was collected`);
      continue;
    }

    const summary = coverageMap.fileCoverageFor(absolutePath).toSummary();
    for (const [metric, threshold] of Object.entries(expected)) {
      const actual = summary[metric as keyof typeof summary].pct;
      if (actual < threshold) {
        failures.push(
          `${filename}: ${metric} ${actual}% is below ${threshold}%`,
        );
      }
    }
  }

  if (failures.length === 0) {
    return undefined;
  }

  const message = `Component coverage thresholds were not met:\n${failures
    .map((failure) => `- ${failure}`)
    .join("\n")}`;
  console.error(message);
  return new Error(message);
}
