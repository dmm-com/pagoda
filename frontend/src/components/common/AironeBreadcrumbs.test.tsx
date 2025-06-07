import { render, screen } from "@testing-library/react";
import React from "react";

import { AironeBreadcrumbs } from "./AironeBreadcrumbs";

describe("AironeBreadcrumbs", () => {
  it("renders children as breadcrumbs", () => {
    render(
      <AironeBreadcrumbs>
        <span>Home</span>
        <span>Page</span>
      </AironeBreadcrumbs>,
    );
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Page")).toBeInTheDocument();
    expect(screen.getByLabelText("breadcrumb")).toBeInTheDocument();
  });
});
