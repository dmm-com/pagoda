/**
 * @jest-environment jsdom
 */

import { Button } from "@mui/material";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";

import { RateLimitedClickable } from "./RateLimitedClickable";

import { TestWrapper } from "TestWrapper";

describe("RateLimitedClickable", () => {
  test("should pass only 1 handler call during rate limiting", async () => {
    const handleClick = jest.fn();

    // with sufficiently long interval
    render(
      <RateLimitedClickable intervalSec={60} onClick={handleClick}>
        <Button>test button</Button>
      </RateLimitedClickable>,
      {
        wrapper: TestWrapper,
      }
    );

    // multiple handler calls
    await waitFor(() => {
      screen.getByRole("button").click();
      screen.getByRole("button").click();
      screen.getByRole("button").click();
    });

    // but only 1 handler call should be passed
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test("should pass multiple handler call if it doesn't exceed rate limit", async () => {
    const handleClick = jest.fn();

    // with no interval
    render(
      <RateLimitedClickable intervalSec={0} onClick={handleClick}>
        <Button>test button</Button>
      </RateLimitedClickable>,
      {
        wrapper: TestWrapper,
      }
    );

    // multiple handler calls
    await waitFor(() => {
      screen.getByRole("button").click();
      screen.getByRole("button").click();
      screen.getByRole("button").click();
    });

    // multiple handler call should be passed
    expect(handleClick).toHaveBeenCalledTimes(3);
  });
});
