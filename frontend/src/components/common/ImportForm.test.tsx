/**
 * @jest-environment jsdom
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { ImportForm } from "components/common/ImportForm";

describe("ImportForm", () => {
  const file = new File(["key: value"], "test.yml", {
    type: "application/yaml",
  });

  test("should import a file successfully", async () => {
    const handleImport = () => Promise.resolve();

    render(<ImportForm handleImport={handleImport} />, {
      wrapper: TestWrapper,
    });

    // upload a file
    await waitFor(() => {
      fireEvent.change(screen.getByTestId("upload-import-file"), {
        target: { files: [file] },
      });
      screen.getByRole("button", { name: "インポート" }).click();
    });

    expect(
      screen.queryByText("ファイルのアップロードに失敗しました"),
    ).not.toBeInTheDocument();
  });
});
