import { AdvancedSearchResult } from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, render, screen } from "@testing-library/react";

import { useJoinedAttributeRowHeights } from "./useJoinedAttributeRowHeights";

const attrNames = ["RackSpace", "RackSpace.Status", "RackSpace.Owner"];
const joinedAttrSources = {
  "RackSpace.Status": "RackSpace",
  "RackSpace.Owner": "RackSpace",
};
const results: AdvancedSearchResult = { count: 0, totalCount: 0, values: [] };
const disconnect = vi.fn();
const observe = vi.fn();
let notifyResize: () => void;

const Harness = ({
  heights,
  searchResults = results,
}: {
  heights: number[];
  searchResults?: AdvancedSearchResult;
}) => {
  const ref = useJoinedAttributeRowHeights(
    searchResults,
    attrNames,
    joinedAttrSources,
  );
  return (
    <table>
      <tbody ref={ref}>
        <tr>
          <td data-search-attribute="RackSpace">
            <ul className="MuiList-root">
              {heights.map((height, index) => (
                <li
                  key={index}
                  data-testid={`source-${index}`}
                  data-height={height}
                />
              ))}
            </ul>
          </td>
          {["Status", "Owner"].map((name) => (
            <td key={name} data-search-attribute={`RackSpace.${name}`}>
              <ul data-source-attribute="RackSpace">
                {heights.map((_, index) => (
                  <li key={index} data-testid={`${name}-${index}`} />
                ))}
              </ul>
            </td>
          ))}
        </tr>
      </tbody>
    </table>
  );
};

beforeEach(() => {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe = observe;
      disconnect = disconnect;
      constructor(callback: ResizeObserverCallback) {
        notifyResize = () => callback([], this as unknown as ResizeObserver);
      }
    },
  );
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(
    function (this: HTMLElement) {
      return { height: Number(this.dataset.height ?? 0) } as DOMRect;
    },
  );
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

test("matches different source heights, including fractional and empty rows, across joined columns", () => {
  render(<Harness heights={[33, 57.5, 28]} />);
  for (const name of ["Status", "Owner"]) {
    expect(screen.getByTestId(`${name}-0`)).toHaveStyle({ height: "33px" });
    expect(screen.getByTestId(`${name}-1`)).toHaveStyle({ height: "57.5px" });
    expect(screen.getByTestId(`${name}-2`)).toHaveStyle({ height: "28px" });
  }
  expect(observe).toHaveBeenCalledTimes(3);
});

test("updates joined rows when source wrapping or font size changes", () => {
  render(<Harness heights={[33, 33]} />);
  screen.getByTestId("source-0").dataset.height = "81";
  act(() => notifyResize());
  expect(screen.getByTestId("Status-0")).toHaveStyle({ height: "81px" });
  expect(screen.getByTestId("Owner-0")).toHaveStyle({ height: "81px" });
  expect(screen.getByTestId("Status-1")).toHaveStyle({ height: "33px" });
});

test("reconnects for new search results and disconnects on unmount", () => {
  const { rerender, unmount } = render(<Harness heights={[57, 33]} />);
  rerender(<Harness heights={[29]} searchResults={{ ...results }} />);
  expect(screen.getByTestId("Status-0")).toHaveStyle({ height: "29px" });
  expect(screen.queryByTestId("Status-1")).not.toBeInTheDocument();
  expect(disconnect).toHaveBeenCalledTimes(1);
  const target = screen.getByTestId("Status-0");
  unmount();
  expect(disconnect).toHaveBeenCalledTimes(2);
  expect(target.style.height).toBe("");
});
