import fs from "node:fs";
import path from "node:path";

import type { Page, TestInfo } from "@playwright/test";

type Evidence = {
  name: string;
  title: string;
  note: string;
  screenshotPath: string;
};

type TestResult = {
  duration: number;
  expectedStatus: TestInfo["expectedStatus"];
  status: TestInfo["status"];
  title: string;
};

const reportDir = path.join(__dirname, "test-results", "report");
const screenshotDir = path.join(reportDir, "screenshots");
const evidence: Evidence[] = [];
const testResults: TestResult[] = [];

export const resetE2eReport = () => {
  fs.rmSync(reportDir, { recursive: true, force: true });
  evidence.length = 0;
  testResults.length = 0;
};

export const recordTestResult = (testInfo: TestInfo) => {
  testResults.push({
    duration: testInfo.duration,
    expectedStatus: testInfo.expectedStatus,
    status: testInfo.status,
    title: testInfo.title,
  });
};

export const captureEvidence = async (
  page: Page,
  testInfo: TestInfo,
  {
    name,
    title,
    note,
  }: {
    name: string;
    title: string;
    note: string;
  },
) => {
  fs.mkdirSync(screenshotDir, { recursive: true });
  const screenshotPath = path.join(screenshotDir, `${name}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await testInfo.attach(title, {
    path: screenshotPath,
    contentType: "image/png",
  });
  evidence.push({
    name,
    title,
    note,
    screenshotPath: path.relative(reportDir, screenshotPath),
  });
};

export const writeE2eReport = () => {
  fs.mkdirSync(reportDir, { recursive: true });
  const lines = [
    "# Pagoda E2E Report",
    "",
    `Generated: ${new Date().toISOString()}`,
    "",
    "## Summary",
    "",
    "- The real frontend bundle booted in Chromium headless mode.",
    "- Dashboard, model list, entry list, and entry detail routes were exercised.",
    "- Object, array-object, named-object, and array-named-object values were verified as entry links.",
    "- Browser console errors, page errors, failed requests, critical axe violations, horizontal overflow, and off-screen interactive controls were checked.",
    "",
    "## Test Results",
    "",
    "| Result | Test case | Duration |",
    "| --- | --- | ---: |",
    ...testResults.map((result) => {
      const status = result.status === result.expectedStatus ? "PASS" : "FAIL";
      const title = result.title.replaceAll("|", "\\|");
      return `| ${status} | ${title} | ${result.duration} ms |`;
    }),
    "",
    "## Evidence",
    "",
  ];

  for (const item of evidence) {
    lines.push(`### ${item.title}`);
    lines.push("");
    lines.push(item.note);
    lines.push("");
    lines.push(`![${item.title}](${item.screenshotPath})`);
    lines.push("");
  }

  fs.writeFileSync(path.join(reportDir, "report.md"), lines.join("\n"));
};
