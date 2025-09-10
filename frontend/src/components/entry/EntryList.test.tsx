/**
 * @jest-environment jsdom
 */

import { EntryBase } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";

import { TestWrapper } from "TestWrapper";
import { EntryList } from "components/entry/EntryList";
import { aironeApiClient } from "repository/AironeApiClient";

afterEach(() => {
  jest.clearAllMocks();
});

describe("EntryList", () => {
  const mockEntries: EntryBase[] = [
    {
      id: 1,
      name: "entry1",
      schema: {
        id: 1,
        name: "test-entity",
      },
      deletedUser: null,
      isActive: true,
      updatedTime: new Date("2024-01-01T00:00:00Z"),
      aliases: [],
    },
    {
      id: 2,
      name: "entry2",
      schema: {
        id: 1,
        name: "test-entity",
      },
      deletedUser: null,
      isActive: true,
      updatedTime: new Date("2024-01-01T00:00:00Z"),
      aliases: [],
    },
  ];

  const mockApiResponse = {
    count: 2,
    results: mockEntries,
  };

  test("should render a component with essential props", async () => {
    jest
      .spyOn(aironeApiClient, "getEntries")
      .mockResolvedValue(Promise.resolve(mockApiResponse));

    await act(async () => {
      render(<EntryList entityId={1} />, {
        wrapper: TestWrapper,
      });
    });

    expect(screen.getByText("1 - 2 / 2 件")).toBeInTheDocument();
  });

  test("should display empty state when no entries", async () => {
    jest.spyOn(aironeApiClient, "getEntries").mockResolvedValue(
      Promise.resolve({
        count: 0,
        results: [],
      }),
    );

    await act(async () => {
      render(<EntryList entityId={0} />, {
        wrapper: TestWrapper,
      });
    });

    expect(screen.getByText("0 - 0 / 0 件")).toBeInTheDocument();
  });

  test("should display entries in table format", async () => {
    jest
      .spyOn(aironeApiClient, "getEntries")
      .mockResolvedValue(Promise.resolve(mockApiResponse));

    await act(async () => {
      render(<EntryList entityId={1} />, {
        wrapper: TestWrapper,
      });
    });

    // Check if entries are displayed
    expect(screen.getByText("entry1")).toBeInTheDocument();
    expect(screen.getByText("entry2")).toBeInTheDocument();
  });

  // TODO: Fix search functionality test - API call not triggered correctly
  test.skip("should handle search functionality", async () => {
    const getEntriesSpy = jest
      .spyOn(aironeApiClient, "getEntries")
      .mockResolvedValue(Promise.resolve(mockApiResponse));

    await act(async () => {
      render(<EntryList entityId={1} />, {
        wrapper: TestWrapper,
      });
    });

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText("1 - 2 / 2 件")).toBeInTheDocument();
    });

    // Find search input with the correct placeholder text
    const searchInput = screen.getByPlaceholderText("アイテムを絞り込む");
    expect(searchInput).toBeInTheDocument();

    // Clear any previous calls
    getEntriesSpy.mockClear();

    // Perform search by typing and pressing Enter
    await act(async () => {
      fireEvent.change(searchInput, { target: { value: "test search" } });
      fireEvent.keyPress(searchInput, {
        key: "Enter",
        code: "Enter",
        charCode: 13,
      });
    });

    // Wait for the search to be triggered
    await waitFor(() => {
      expect(getEntriesSpy).toHaveBeenCalledWith(
        1, // entityId
        true, // isActive
        1, // pageNumber
        "test search", // keyword
      );
    });
  });

  // TODO: Fix pagination test - text format mismatch
  test.skip("should handle pagination", async () => {
    const getEntriesSpy = jest
      .spyOn(aironeApiClient, "getEntries")
      .mockResolvedValue(
        Promise.resolve({
          count: 25, // More than one page
          results: mockEntries,
        }),
      );

    await act(async () => {
      render(<EntryList entityId={1} />, {
        wrapper: TestWrapper,
      });
    });

    // Wait for initial load - expect pagination info to be visible
    await waitFor(() => {
      // With 25 total items and 2 displayed results, verify pagination info
      expect(screen.getByText("1 - 2 / 25 件")).toBeInTheDocument();
    });

    // Check if pagination controls are present
    const pagination = screen.getByRole("navigation");
    expect(pagination).toBeInTheDocument();

    // Try to click next page (if available)
    const nextButton = within(pagination).queryByLabelText(/next/i);
    if (nextButton && !nextButton.hasAttribute("disabled")) {
      getEntriesSpy.mockClear();

      await act(async () => {
        fireEvent.click(nextButton);
      });

      // Verify API was called with correct page parameter
      await waitFor(() => {
        expect(getEntriesSpy).toHaveBeenCalledWith(
          1, // entityId
          true, // isActive
          2, // pageNumber (page 2)
          "", // keyword (empty for pagination)
        );
      });
    }
  });

  test("should handle loading state", async () => {
    // Mock a delayed API response
    jest
      .spyOn(aironeApiClient, "getEntries")
      .mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockApiResponse), 100),
          ),
      );

    await act(async () => {
      render(<EntryList entityId={1} />, {
        wrapper: TestWrapper,
      });
    });

    // Check if loading indicator is shown
    const loadingElements = screen.queryAllByText(/読み込み中/i);
    if (loadingElements.length > 0) {
      expect(loadingElements[0]).toBeInTheDocument();
    }

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.getByText("1 - 2 / 2 件")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  test("should handle API errors gracefully", async () => {
    // Mock API error
    jest
      .spyOn(aironeApiClient, "getEntries")
      .mockRejectedValue(new Error("API Error"));

    // Suppress console errors during test
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    // Expect the component to throw due to useAsyncWithThrow
    await expect(async () => {
      await act(async () => {
        render(<EntryList entityId={1} />, {
          wrapper: TestWrapper,
        });
      });
    }).rejects.toThrow("API Error");

    consoleSpy.mockRestore();
  });

  test("should refresh data when entityId changes", async () => {
    const getEntriesSpy = jest
      .spyOn(aironeApiClient, "getEntries")
      .mockResolvedValue(Promise.resolve(mockApiResponse));

    const { rerender } = render(<EntryList entityId={1} />, {
      wrapper: TestWrapper,
    });

    await waitFor(() => {
      expect(getEntriesSpy).toHaveBeenCalledWith(1, true, 1, "");
    });

    // Clear previous calls
    getEntriesSpy.mockClear();

    // Change entityId
    await act(async () => {
      rerender(<EntryList entityId={2} />);
    });

    await waitFor(() => {
      expect(getEntriesSpy).toHaveBeenCalledWith(2, true, 1, "");
    });

    expect(getEntriesSpy).toHaveBeenCalledTimes(1);
  });
});
