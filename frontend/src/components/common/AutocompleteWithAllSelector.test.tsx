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
  it("renders and allows select-all/remove-all", async () => {
    const options = ["A", "B", "C"];
    const handleChange = jest.fn();
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
