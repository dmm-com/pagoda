import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { CommonImportModal } from "./CommonImportModal";

import type { Mock } from "vitest";

import { TestWrapper } from "TestWrapper";
import { aironeApiClient } from "repository/AironeApiClient";

vi.mock("repository/AironeApiClient", () => ({
  aironeApiClient: {
    importCommon: vi.fn(),
    startCommonImportPreview: vi.fn(),
  },
}));

// The form decodes the file's bytes before handing them over; jsdom has no
// File.arrayBuffer and the decoder is not what these tests are about.
const mockEncoding = vi.hoisted(() => ({
  detect: vi.fn().mockReturnValue("UTF-8"),
  convert: vi.fn().mockReturnValue("[]"),
}));
vi.mock("encoding-japanese", () => ({
  default: mockEncoding,
  ...mockEncoding,
}));

beforeEach(() => {
  File.prototype.arrayBuffer = vi.fn().mockResolvedValue(new ArrayBuffer(8));
});

afterEach(() => {
  vi.clearAllMocks();
});

const getFileInput = (): HTMLInputElement =>
  screen
    .getByTestId("upload-import-file")
    .querySelector('input[type="file"]') as HTMLInputElement;

describe("CommonImportModal", () => {
  const defaultProps = {
    openImportModal: true,
    closeImportModal: vi.fn(),
  };

  test("renders the title, description and caption", () => {
    render(<CommonImportModal {...defaultProps} />, { wrapper: TestWrapper });

    expect(screen.getByText("データのインポート")).toBeInTheDocument();
    expect(
      screen.getByText("インポートするファイルを選択してください。"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "※ファイルの内容からモデル・アイテム・ユーザ・グループ・ロールを自動判定します。CSV形式のファイルは選択できません。",
      ),
    ).toBeInTheDocument();
  });

  test("renders nothing when openImportModal is false", () => {
    render(<CommonImportModal {...defaultProps} openImportModal={false} />, {
      wrapper: TestWrapper,
    });

    expect(screen.queryByText("データのインポート")).not.toBeInTheDocument();
  });

  test("calls closeImportModal when cancel is clicked", () => {
    render(<CommonImportModal {...defaultProps} />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByRole("button", { name: "キャンセル" }));

    expect(defaultProps.closeImportModal).toHaveBeenCalledTimes(1);
  });

  test("offers a preview button", () => {
    render(<CommonImportModal {...defaultProps} />, { wrapper: TestWrapper });

    expect(
      screen.getByRole("button", { name: "変更内容を確認" }),
    ).toBeInTheDocument();
  });

  test("shows the server's reason when a preview cannot be started", async () => {
    (aironeApiClient.startCommonImportPreview as Mock).mockResolvedValue({
      jobIds: [],
      errors: ["unknown model: Foo"],
    });

    render(<CommonImportModal {...defaultProps} />, { wrapper: TestWrapper });

    fireEvent.change(getFileInput(), {
      target: {
        files: [new File(["[]"], "import.yaml", { type: "application/yaml" })],
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "変更内容を確認" }));

    expect(await screen.findByText("unknown model: Foo")).toBeInTheDocument();
    expect(aironeApiClient.startCommonImportPreview).toHaveBeenCalledTimes(1);
    expect(aironeApiClient.importCommon).not.toHaveBeenCalled();
  });

  test("shows the server's reason when no job was started", async () => {
    (aironeApiClient.importCommon as Mock).mockResolvedValue({
      type: "entry",
      jobIds: [],
      error: ["unknown model: Foo"],
    });

    render(<CommonImportModal {...defaultProps} />, { wrapper: TestWrapper });

    const file = new File(["[]"], "import.yaml", { type: "application/yaml" });
    fireEvent.change(getFileInput(), {
      target: { files: [file] },
    });
    fireEvent.click(screen.getByRole("button", { name: "インポート" }));

    expect(await screen.findByText("unknown model: Foo")).toBeInTheDocument();
    expect(aironeApiClient.importCommon).toHaveBeenCalledTimes(1);
    expect(defaultProps.closeImportModal).not.toHaveBeenCalled();
  });

  test("passes the force option when the checkbox is checked", async () => {
    (aironeApiClient.importCommon as Mock).mockResolvedValue({
      type: "entry",
      jobIds: [1],
      error: [],
    });

    render(<CommonImportModal {...defaultProps} />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByTestId("force-import"));
    fireEvent.change(getFileInput(), {
      target: {
        files: [new File(["[]"], "import.yaml", { type: "application/yaml" })],
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "インポート" }));

    await waitFor(() =>
      expect(aironeApiClient.importCommon).toHaveBeenCalledWith(
        expect.anything(),
        true,
        undefined,
      ),
    );
  });

  test("does not report an error when a job was started", async () => {
    (aironeApiClient.importCommon as Mock).mockResolvedValue({
      type: "group",
      jobIds: [1],
      error: [],
    });

    render(<CommonImportModal {...defaultProps} />, { wrapper: TestWrapper });

    const file = new File(["- id: 1"], "import.yaml", {
      type: "application/yaml",
    });
    fireEvent.change(getFileInput(), {
      target: { files: [file] },
    });
    fireEvent.click(screen.getByRole("button", { name: "インポート" }));

    await waitFor(() =>
      expect(aironeApiClient.importCommon).toHaveBeenCalledTimes(1),
    );
    expect(
      screen.queryByText("ファイルのアップロードに失敗しました"),
    ).not.toBeInTheDocument();
  });
});
