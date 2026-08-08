import { Page } from "@playwright/test";

/**
 * Helpers for talking to the real server from the live suite.
 *
 * The requests are issued from the page itself so that they carry the very same
 * session and CSRF cookies the UI uses.
 */

export const username = process.env.E2E_USERNAME ?? "admin";
const password = process.env.E2E_PASSWORD ?? "admin";

export const login = async (page: Page) => {
  await page.goto("/auth/login/");
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL(/\/ui\//);
};

export const apiGet = async <T>(page: Page, url: string): Promise<T> =>
  page.evaluate(async (target) => {
    const response = await fetch(target, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      throw new Error(`GET ${target} failed with ${response.status}`);
    }
    return response.json();
  }, url);

export const postJson = async (
  page: Page,
  url: string,
  body: unknown,
): Promise<void> =>
  page.evaluate(
    async ({ target, payload }) => {
      const csrfToken =
        document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/)?.[1] ?? "";
      const response = await fetch(target, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": decodeURIComponent(csrfToken),
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(
          `POST ${target} failed with ${response.status}: ${await response.text()}`,
        );
      }
    },
    { target: url, payload: body },
  );

export const postYaml = async (
  page: Page,
  url: string,
  body: string,
): Promise<void> =>
  page.evaluate(
    async ({ target, payload }) => {
      const csrfToken =
        document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/)?.[1] ?? "";
      const response = await fetch(target, {
        method: "POST",
        headers: {
          "Content-Type": "application/yaml",
          "X-CSRFToken": decodeURIComponent(csrfToken),
        },
        body: payload,
      });
      if (!response.ok) {
        throw new Error(
          `POST ${target} failed with ${response.status}: ${await response.text()}`,
        );
      }
    },
    { target: url, payload: body },
  );
