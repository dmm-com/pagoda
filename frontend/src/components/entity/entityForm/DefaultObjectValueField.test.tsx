import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { useState } from "react";

import { DefaultObjectValueField } from "./DefaultObjectValueField";

import { TestWrapper } from "TestWrapper";
import { aironeApiClient } from "repository/AironeApiClient";

const Harness = ({ multiple = false }: { multiple?: boolean }) => {
  const [value, setValue] = useState<number | number[] | null>(
    multiple ? [] : null,
  );
  return (
    <>
      <DefaultObjectValueField
        value={value}
        referralEntityIds={[10]}
        multiple={multiple}
        disabled={false}
        ariaLabel="object default"
        onChange={setValue}
      />
      <output data-testid="value">{JSON.stringify(value)}</output>
    </>
  );
};

describe("DefaultObjectValueField", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(aironeApiClient, "getEntries").mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        { id: 101, name: "Primary server" },
        { id: 102, name: "Secondary server" },
      ],
    });
  });

  test("stores a single selected Entry as its ID", async () => {
    render(<Harness />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    const listbox = await screen.findByRole("listbox");
    fireEvent.click(within(listbox).getByText("Primary server"));

    expect(screen.getByTestId("value")).toHaveTextContent("101");
    expect(aironeApiClient.getEntries).toHaveBeenCalledWith(10, true, 1, "");
  });

  test("stores multiple selected Entries as an ordered ID list", async () => {
    render(<Harness multiple />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    let listbox = await screen.findByRole("listbox");
    fireEvent.click(within(listbox).getByText("Secondary server"));
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    listbox = await screen.findByRole("listbox");
    fireEvent.click(within(listbox).getByText("Primary server"));

    await waitFor(() =>
      expect(screen.getByTestId("value")).toHaveTextContent("[102,101]"),
    );
  });
});
