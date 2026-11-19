import { act, fireEvent, render, screen } from "@testing-library/react";

import { ExportButton } from "./ExportButton";

import { TestWrapper } from "TestWrapper";

beforeEach(() => {
  localStorage.clear();
});

describe("ExportButton", () => {
  test("registers only one export across tabs during the debounce window", async () => {
    localStorage.clear();
    let resolveFirstExport!: () => void;
    const firstExport = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveFirstExport = resolve;
        }),
    );
    const secondExport = vi.fn().mockResolvedValue(undefined);
    render(
      <>
        <ExportButton onExport={firstExport} />
        <ExportButton onExport={secondExport} />
      </>,
      { wrapper: TestWrapper },
    );

    fireEvent.click(screen.getAllByRole("button", { name: "エクスポート" })[0]);
    fireEvent.click(screen.getAllByRole("button", { name: "エクスポート" })[1]);

    expect(firstExport).toHaveBeenCalledTimes(1);
    expect(secondExport).not.toHaveBeenCalled();

    await act(async () => resolveFirstExport());
  });

  test("allows another export when the 15-second debounce expires", async () => {
    const start = Date.UTC(2026, 0, 1);
    const clock = vi.spyOn(Date, "now").mockReturnValue(start);
    try {
      const onExport = vi.fn().mockResolvedValue(undefined);
      render(<ExportButton onExport={onExport} />, { wrapper: TestWrapper });
      const button = screen.getByRole("button", { name: "エクスポート" });
      const clickExport = () =>
        act(async () => {
          fireEvent.click(button);
        });

      await clickExport();
      clock.mockReturnValue(start + 14_999);
      await clickExport();
      expect(onExport).toHaveBeenCalledTimes(1);

      clock.mockReturnValue(start + 15_000);
      await clickExport();
      expect(onExport).toHaveBeenCalledTimes(2);
    } finally {
      clock.mockRestore();
    }
  });

  test("notifies success only after the export job is registered", async () => {
    let resolveExport!: () => void;
    const onExport = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveExport = resolve;
        }),
    );
    render(<ExportButton onExport={onExport} />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByRole("button", { name: "エクスポート" }));

    expect(onExport).toHaveBeenCalledTimes(1);
    expect(
      screen.queryByText("エクスポートのジョブ登録に成功しました"),
    ).not.toBeInTheDocument();

    await act(async () => resolveExport());

    expect(
      await screen.findByText("エクスポートのジョブ登録に成功しました"),
    ).toBeInTheDocument();
  });

  test("notifies failure when the export job cannot be registered", async () => {
    const onExport = vi.fn().mockRejectedValue(new Error("export failed"));
    render(<ExportButton onExport={onExport} />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByRole("button", { name: "エクスポート" }));

    expect(
      await screen.findByText("エクスポートのジョブ登録に失敗しました"),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("エクスポートのジョブ登録に成功しました"),
    ).not.toBeInTheDocument();
    expect(onExport).toHaveBeenCalledTimes(1);
  });
});
