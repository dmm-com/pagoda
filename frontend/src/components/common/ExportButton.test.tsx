import { act, fireEvent, render, screen } from "@testing-library/react";

import { ExportButton } from "./ExportButton";

import { TestWrapper } from "TestWrapper";

describe("ExportButton", () => {
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
