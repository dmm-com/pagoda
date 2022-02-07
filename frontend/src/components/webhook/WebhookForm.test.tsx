/**
 * @jest-environment jsdom
 */

import { render, waitFor } from "@testing-library/react";
import React from "react";

import { WebhookForm } from "components/webhook/WebhookForm";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", async () => {
  /* eslint-disable */
  jest
    .spyOn(require("../../utils/AironeAPIClient"), "getWebhooks")
    .mockResolvedValueOnce({
      json() {
        return Promise.resolve([]);
      },
    });
  /* eslint-enable */

  await waitFor(() => {
    expect(() =>
      render(<WebhookForm entityId={0} />, { wrapper: TestWrapper })
    ).not.toThrow();
  });

  jest.clearAllMocks();
});
