/**
 * @jest-environment jsdom
 */

import { act, render, screen, within } from "@testing-library/react";

import { TestWrapper } from "TestWrapper";
import { EntrySelfHistoryList } from "components/entry/EntrySelfHistoryList";

// Mock the API client
jest.mock("repository/AironeApiClient");

// Mock the router navigate
const mockNavigate = jest.fn();
jest.mock("react-router", () => ({
  ...jest.requireActual("react-router"),
  useNavigate: () => mockNavigate,
}));

describe("EntrySelfHistoryList", () => {
  const mockHistories = {
    count: 3,
    results: [
      {
        history_id: 3,
        name: "updated_name_2",
        prev_name: "updated_name_1",
        history_date: "2023-01-03T12:00:00+09:00",
        history_user: "user2",
        history_type: "~", // update
      },
      {
        history_id: 2,
        name: "updated_name_1",
        prev_name: "original_name",
        history_date: "2023-01-02T12:00:00+09:00",
        history_user: "user1",
        history_type: "~", // update
      },
      {
        history_id: 1,
        name: "original_name",
        prev_name: null,
        history_date: "2023-01-01T12:00:00+09:00",
        history_user: "system",
        history_type: "+", // creation
      },
    ],
  };

  const mockProps = {
    entityId: 1,
    entryId: 2,
    histories: mockHistories,
    page: 1,
    changePage: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("should render entry self histories correctly", async () => {
    await act(async () => {
      render(<EntrySelfHistoryList {...mockProps} />, {
        wrapper: TestWrapper,
      });
    });

    // Check table headers
    expect(screen.getByText("操作")).toBeInTheDocument();
    expect(screen.getByText("変更前のアイテム名")).toBeInTheDocument();
    expect(screen.getByText("変更後のアイテム名")).toBeInTheDocument();
    expect(screen.getByText("実行日時")).toBeInTheDocument();
    expect(screen.getByText("実行者")).toBeInTheDocument();
    expect(screen.getByText("復旧")).toBeInTheDocument();

    // Check table body content
    const bodyRowGroup = screen.getAllByRole("rowgroup")[1];
    const rows = within(bodyRowGroup).getAllByRole("row");
    expect(rows).toHaveLength(3);

    // Check first row (latest record)
    expect(within(rows[0]).getByText("更新")).toBeInTheDocument();
    expect(within(rows[0]).getByText("updated_name_1")).toBeInTheDocument();
    expect(within(rows[0]).getByText("updated_name_2")).toBeInTheDocument();
    expect(within(rows[0]).getByText("user2")).toBeInTheDocument();

    // Check second row
    expect(within(rows[1]).getByText("更新")).toBeInTheDocument();
    expect(within(rows[1]).getByText("original_name")).toBeInTheDocument();
    expect(within(rows[1]).getByText("updated_name_1")).toBeInTheDocument();
    expect(within(rows[1]).getByText("user1")).toBeInTheDocument();

    // Check third row (creation record)
    expect(within(rows[2]).getByText("作成")).toBeInTheDocument();
    expect(within(rows[2]).getByText("-")).toBeInTheDocument(); // prev_name is null
    expect(within(rows[2]).getByText("original_name")).toBeInTheDocument();
    expect(within(rows[2]).getByText("system")).toBeInTheDocument();
  });

  test("should disable restore button for latest record", async () => {
    await act(async () => {
      render(<EntrySelfHistoryList {...mockProps} />, {
        wrapper: TestWrapper,
      });
    });

    const restoreButtons = screen.getAllByRole("button");
    // Filter buttons that contain RestoreIcon (look for SVG with specific data-testid)
    const restoreIconButtons = restoreButtons.filter((button) => {
      const svgElements = button.querySelectorAll("svg");
      return Array.from(svgElements).some(
        (svg) => svg.getAttribute("data-testid") === "RestoreIcon",
      );
    });

    // Should have 3 restore buttons
    expect(restoreIconButtons).toHaveLength(3);

    // First button (latest record) should be disabled
    expect(restoreIconButtons[0]).toBeDisabled();

    // Other buttons should be enabled
    expect(restoreIconButtons[1]).toBeEnabled();
    expect(restoreIconButtons[2]).toBeEnabled();
  });

  test("should show correct history type labels", async () => {
    await act(async () => {
      render(<EntrySelfHistoryList {...mockProps} />, {
        wrapper: TestWrapper,
      });
    });

    expect(screen.getAllByText("更新")).toHaveLength(2);
    expect(screen.getByText("作成")).toBeInTheDocument();
  });

  test("should handle empty histories", async () => {
    const emptyHistories = {
      count: 0,
      results: [],
    };

    await act(async () => {
      render(
        <EntrySelfHistoryList {...mockProps} histories={emptyHistories} />,
        { wrapper: TestWrapper },
      );
    });

    // Should still show headers
    expect(screen.getByText("操作")).toBeInTheDocument();

    // Should not show any data rows
    const bodyRowGroup = screen.getAllByRole("rowgroup")[1];
    expect(within(bodyRowGroup).queryAllByRole("row")).toHaveLength(0);
  });

  test("should format dates correctly", async () => {
    await act(async () => {
      render(<EntrySelfHistoryList {...mockProps} />, {
        wrapper: TestWrapper,
      });
    });

    // Check that dates are present (exact format may depend on locale)
    // We just check that the date content is rendered without asserting specific format
    const dateElements = screen.getAllByText(/2023/);
    expect(dateElements.length).toBeGreaterThan(0);
  });

  test("should handle pagination", async () => {
    await act(async () => {
      render(<EntrySelfHistoryList {...mockProps} />, {
        wrapper: TestWrapper,
      });
    });

    // Should render PaginationFooter
    expect(screen.getByRole("navigation")).toBeInTheDocument();
  });
});
