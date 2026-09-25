/**
 */

import { act, render, screen } from "@testing-library/react";

import { UnavailableErrorPage } from "./UnavailableErrorPage";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

afterEach(() => {
  vi.clearAllMocks();
});

test("should match snapshot", async () => {
  // wait async calls and get rendered fragment
  const result = render(<UnavailableErrorPage />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  render(<UnavailableErrorPage />, { wrapper: TestWrapper });

  expect(screen.getByText("Unavailable:;(∩´﹏`∩);:")).toBeInTheDocument();
  expect(
    screen.getByText("This page is currently unavailable."),
  ).toBeInTheDocument();
  expect(
    screen.getByText(
      "Please check announcements from your administrator or contact them.",
    ),
  ).toBeInTheDocument();
});
