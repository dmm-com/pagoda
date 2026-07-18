const path = require("node:path");

const { createCoverageMap } = require("istanbul-lib-coverage");

const thresholds = {
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

class FrontendCoverageReporter {
  constructor(globalConfig) {
    this.enabled = globalConfig.collectCoverage;
    this.rootDir = globalConfig.rootDir;
    this.coverageMap = createCoverageMap({});
    this.error = undefined;
  }

  onTestResult(_test, testResult) {
    if (testResult.coverage) this.coverageMap.merge(testResult.coverage);
  }

  onRunComplete() {
    if (!this.enabled) return;

    const failures = [];

    for (const [filename, expected] of Object.entries(thresholds)) {
      const absolutePath = path.resolve(this.rootDir, filename);
      if (!this.coverageMap.data[absolutePath]) {
        failures.push(`${filename}: no coverage was collected`);
        continue;
      }

      const summary = this.coverageMap.fileCoverageFor(absolutePath).toSummary();
      for (const [metric, threshold] of Object.entries(expected)) {
        const actual = summary[metric].pct;
        if (actual < threshold) {
          failures.push(
            `${filename}: ${metric} ${actual}% is below ${threshold}%`,
          );
        }
      }
    }

    if (failures.length > 0) {
      this.error = new Error(
        `Component coverage thresholds were not met:\n${failures
          .map((failure) => `- ${failure}`)
          .join("\n")}`,
      );
      console.error(this.error.message);
    }
  }

  getLastError() {
    return this.error;
  }
}

module.exports = FrontendCoverageReporter;
