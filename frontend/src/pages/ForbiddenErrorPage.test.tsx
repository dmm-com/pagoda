/**
 */

import { act, render, screen } from "@testing-library/react";

import { ForbiddenErrorPage } from "./ForbiddenErrorPage";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

afterEach(() => {
  vi.clearAllMocks();
});

test("should match snapshot", async () => {
  // wait async calls and get rendered fragment
  const result = render(<ForbiddenErrorPage />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  render(<ForbiddenErrorPage />, { wrapper: TestWrapper });

  expect(screen.getByText("Forbidden… (|| ﾟДﾟ)")).toBeInTheDocument();
  expect(
    screen.getByText("You do not have permission to view this page."),
  ).toBeInTheDocument();
  expect(
    screen.getByText("The page administrator may be able to grant you access."),
  ).toBeInTheDocument();
});
