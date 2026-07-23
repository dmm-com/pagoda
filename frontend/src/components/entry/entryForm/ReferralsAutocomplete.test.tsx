/**
 * @jest-environment jsdom
 */

import { GetEntryAttrReferral } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { useState } from "react";

import { aironeApiClient } from "../../../repository/AironeApiClient";

import { ReferralsAutocomplete } from "./ReferralsAutocomplete";

import { TestWrapper } from "TestWrapper";

const options: GetEntryAttrReferral[] = [
  { id: 1, name: "Entry one", displayLabel: "Display one" },
  { id: 2, name: "Entry two", displayLabel: null },
];

const Harness = ({
  initialValue = null,
  multiple = false,
  disabled = false,
  error,
}: {
  initialValue?: GetEntryAttrReferral | GetEntryAttrReferral[] | null;
  multiple?: boolean;
  disabled?: boolean;
  error?: { message?: string };
}) => {
  const [value, setValue] = useState(initialValue);
  return (
    <>
      <ReferralsAutocomplete
        attrId={7}
        value={value}
        handleChange={setValue}
        multiple={multiple}
        isDisabled={disabled}
        error={error}
      />
      <output data-testid="value">{JSON.stringify(value)}</output>
    </>
  );
};

describe("ReferralsAutocomplete", () => {
  beforeEach(() => {
    jest.restoreAllMocks();
  });

  test("fetches once on open and uses display labels with name fallback", async () => {
    const fetchSpy = jest
      .spyOn(aironeApiClient, "getEntryAttrReferrals")
      .mockResolvedValue(options);
    render(<Harness />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    const listbox = await screen.findByRole("listbox");
    expect(within(listbox).getByText("Display one")).toBeInTheDocument();
    expect(within(listbox).getByText("Entry two")).toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalledWith(7);

    fireEvent.click(screen.getByRole("option", { name: "Display one" }));
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    await screen.findByRole("listbox");
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  test("stores a selected option and restores its label after blur", async () => {
    const fetchSpy = jest
      .spyOn(aironeApiClient, "getEntryAttrReferrals")
      .mockResolvedValue(options);
    render(<Harness />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    fireEvent.click(await screen.findByRole("option", { name: "Display one" }));
    expect(screen.getByTestId("value")).toHaveTextContent(
      '"displayLabel":"Display one"',
    );

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "temporary text" } });
    fireEvent.blur(input);
    expect(input).toHaveValue("Display one");
    await waitFor(() =>
      expect(fetchSpy).toHaveBeenCalledWith(7, "temporary text"),
    );
    await waitFor(() =>
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument(),
    );
  });

  test("queries by input and clears the single value", async () => {
    const fetchSpy = jest
      .spyOn(aironeApiClient, "getEntryAttrReferrals")
      .mockResolvedValue(options);
    render(<Harness initialValue={options[0]} />, { wrapper: TestWrapper });

    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "two" },
    });
    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith(7, "two"));

    fireEvent.click(screen.getByTitle("Clear"));
    expect(screen.getByTestId("value")).toHaveTextContent("null");
    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith(7, ""));
    await waitFor(() =>
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument(),
    );
  });

  test("clears multiple values to an empty array", async () => {
    const fetchSpy = jest
      .spyOn(aironeApiClient, "getEntryAttrReferrals")
      .mockResolvedValue(options);
    render(<Harness initialValue={options} multiple />, {
      wrapper: TestWrapper,
    });

    expect(screen.getByText("Display one")).toBeInTheDocument();
    expect(screen.getByText("Entry two")).toBeInTheDocument();
    fireEvent.click(screen.getByTitle("Clear"));
    expect(screen.getByTestId("value")).toHaveTextContent("[]");
    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith(7, ""));
    await waitFor(() =>
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument(),
    );
  });

  test("recovers from request failures and leaves the picker usable", async () => {
    jest
      .spyOn(aironeApiClient, "getEntryAttrReferrals")
      .mockRejectedValue(new Error("network unavailable"));
    render(<Harness />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    await waitFor(() =>
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument(),
    );
    expect(screen.getByRole("combobox")).toBeEnabled();
  });

  test("renders validation feedback and disabled state", () => {
    jest
      .spyOn(aironeApiClient, "getEntryAttrReferrals")
      .mockResolvedValue(options);
    render(<Harness disabled error={{ message: "Selection is required" }} />, {
      wrapper: TestWrapper,
    });

    expect(screen.getByText("Selection is required")).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toBeDisabled();
  });
});
