import { AxeBuilder } from "@axe-core/playwright";
import { expect, Page, TestInfo } from "@playwright/test";

export const collectBrowserFailures = (page: Page) => {
  const failures: string[] = [];
  const successfulResponses = new WeakSet<object>();

  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      if (
        message
          .text()
          .includes("Received `%s` for a non-boolean attribute `%s`")
      ) {
        return;
      }
      failures.push(`console ${message.type()}: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => {
    failures.push(`page error: ${error.message}`);
  });
  page.on("response", (response) => {
    if (response.ok()) {
      successfulResponses.add(response.request());
    }
  });
  page.on("requestfailed", (request) => {
    // A response can be accepted successfully while its empty response body is
    // aborted by a subsequent list refresh. Keep real transport failures, but
    // do not report a request that already received a successful HTTP response.
    if (successfulResponses.has(request)) return;
    const failure = request.failure();
    failures.push(
      `request failed: ${request.method()} ${request.url()} ${failure?.errorText ?? ""}`,
    );
  });

  return failures;
};

export const expectNoBrowserFailures = (failures: string[]) => {
  expect(failures).toEqual([]);
};

export const expectUiQualityGate = async (page: Page, testInfo: TestInfo) => {
  const viewport = page.viewportSize();
  const pageSize = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(pageSize.scrollWidth).toBeLessThanOrEqual(pageSize.clientWidth + 1);

  const offscreenControls = await page
    .locator("button, a[href], input, select, textarea, [role='button']")
    .evaluateAll((elements) =>
      elements
        .map((element) => {
          const rect = element.getBoundingClientRect();
          return {
            text:
              element.getAttribute("aria-label") ??
              element.textContent?.trim() ??
              element.tagName,
            left: rect.left,
            right: rect.right,
            top: rect.top,
            bottom: rect.bottom,
          };
        })
        .filter((rect) => rect.right < -1 || rect.left > window.innerWidth + 1),
    );
  expect(offscreenControls).toEqual([]);

  const axeResults = await new AxeBuilder({ page })
    .disableRules(["button-name", "color-contrast", "label", "list"])
    .analyze();
  const severeViolations = axeResults.violations.filter((violation) =>
    ["critical", "serious"].includes(violation.impact ?? ""),
  );

  if (severeViolations.length > 0) {
    await testInfo.attach("axe-violations", {
      body: JSON.stringify(severeViolations, null, 2),
      contentType: "application/json",
    });
  }

  expect(severeViolations).toEqual([]);
  expect(viewport?.width ?? 0).toBeGreaterThan(0);
};
