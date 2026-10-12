/**
 */

import { act, render, screen } from "@testing-library/react";

import { NonTermsServiceAgreementPage } from "./NonTermsServiceAgreement";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

afterEach(() => {
  vi.clearAllMocks();
});

test("should match snapshot", async () => {
  // wait async calls and get rendered fragment
  const result = render(<NonTermsServiceAgreementPage />, {
    wrapper: TestWrapper,
  });

  expect(result).toMatchSnapshot();
});

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  render(<NonTermsServiceAgreementPage />, {
    wrapper: TestWrapper,
  });

  expect(
    screen.getByText("You must agree to the terms of service to use this."),
  ).toBeInTheDocument();
  expect(
    screen.getByText("Back to the terms agreement page"),
  ).toBeInTheDocument();
});
