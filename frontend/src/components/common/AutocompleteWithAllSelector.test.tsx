import TextField from "@mui/material/TextField";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";

import { AutocompleteWithAllSelector } from "./AutocompleteWithAllSelector";

describe("AutocompleteWithAllSelector", () => {
  it("preserves the supplied selection on initial render", async () => {
    const handleChange = vi.fn();
    render(
      <AutocompleteWithAllSelector
        selectAllLabel="すべて選択"
        options={["A", "B"]}
        value={["A"]}
        multiple
        onChange={handleChange}
        renderInput={(params) => <TextField {...params} />}
      />,
    );

    expect(screen.getByText("A")).toBeInTheDocument();
    expect(handleChange).not.toHaveBeenCalled();
  });

  it("clears the selection when re-enabled after being disabled", async () => {
    const handleChange = vi.fn();
    const { rerender } = render(
      <AutocompleteWithAllSelector
        selectAllLabel="すべて選択"
        options={["A", "B"]}
        value={["A"]}
        multiple
        disabled
        onChange={handleChange}
        renderInput={(params) => <TextField {...params} />}
      />,
    );

    rerender(
      <AutocompleteWithAllSelector
        selectAllLabel="すべて選択"
        options={["A", "B"]}
        value={["A"]}
        multiple
        disabled={false}
        onChange={handleChange}
        renderInput={(params) => <TextField {...params} />}
      />,
    );

    await waitFor(() => {
      expect(handleChange).toHaveBeenCalledWith(expect.anything(), [], "clear");
    });
  });

  it("renders and allows select-all/remove-all", async () => {
    const options = ["A", "B", "C"];
    const handleChange = vi.fn();
    render(
      <AutocompleteWithAllSelector
        selectAllLabel="すべて選択"
        options={options}
        value={[]}
        multiple
        onChange={handleChange}
        renderInput={(params) => <TextField {...params} />}
      />,
    );
    // open options
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    // select-all option should be present
    await waitFor(() => {
      expect(
        within(document.body).queryAllByText("すべて選択").length,
      ).toBeGreaterThan(0);
    });
  });
});
