import { render, screen } from "@testing-library/react";
import React from "react";

import { AironeModal } from "./AironeModal";

describe("AironeModal", () => {
  it("renders modal with title and children", () => {
    render(
      <AironeModal open={true} onClose={() => {}} title="Test Title">
        <div>Modal Content</div>
      </AironeModal>,
    );
    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(screen.getByText("Modal Content")).toBeInTheDocument();
  });

  it("does not render when open is false", () => {
    render(
      <AironeModal open={false} onClose={() => {}} title="Test Title">
        <div>Modal Content</div>
      </AironeModal>,
    );
    // Modal content should not be visible
    expect(screen.queryByText("Test Title")).not.toBeInTheDocument();
  });
});
