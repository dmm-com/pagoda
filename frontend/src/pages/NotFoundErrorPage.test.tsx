/**
 */

import { act, render, screen } from "@testing-library/react";

import { NotFoundErrorPage } from "./NotFoundErrorPage";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

afterEach(() => {
  vi.clearAllMocks();
});

test("should match snapshot", async () => {
  // wait async calls and get rendered fragment
  const result = render(<NotFoundErrorPage />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  render(<NotFoundErrorPage />, { wrapper: TestWrapper });

  expect(
    screen.getByText(
      "The page you are looking for may have been removed, changed, or is temporarily unavailable.",
    ),
  ).toBeInTheDocument();
  expect(screen.getByText("Back to top")).toBeInTheDocument();
});
