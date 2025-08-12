import { render } from "@testing-library/react";
import React from "react";
import { MemoryRouter } from "react-router";

import { AironeLink } from "./AironeLink";

describe("AironeLink", () => {
  it("renders a styled link", () => {
    const { getByText } = render(
      <MemoryRouter>
        <AironeLink to="/test">Test Link</AironeLink>
      </MemoryRouter>,
    );
    expect(getByText("Test Link")).toBeInTheDocument();
    expect(getByText("Test Link").closest("a")).toHaveAttribute(
      "href",
      "/test",
    );
  });
});
