/**
 * @jest-environment jsdom
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { EntityControlMenu } from "./EntityControlMenu";

import { TestWrapper } from "TestWrapper";
import { aironeApiClient } from "repository/AironeApiClient";
import { ACLType } from "services/ACLUtil";

describe("EntityControlMenu", () => {
  test("should render with essential props", () => {
    expect(() =>
      render(
        <EntityControlMenu
          entityId={1}
          anchorElem={null}
          handleClose={() => {
            /* any closing process */
          }}
          setOpenImportModal={() => false}
        />,
        { wrapper: TestWrapper },
      ),
    ).not.toThrow();
  });

  test("menu items are displayed correctly", () => {
    // specify anchorElem to open the menu
    render(
      <EntityControlMenu
        entityId={1}
        anchorElem={document.createElement("button")}
        handleClose={() => {}}
        setOpenImportModal={() => false}
      />,
      { wrapper: TestWrapper },
    );

    // menu items text should be displayed
    expect(screen.getByText("アイテム一覧")).toBeInTheDocument();
    expect(screen.getByText("エイリアス一覧")).toBeInTheDocument();
    expect(screen.getByText("編集")).toBeInTheDocument();
    expect(screen.getByText("ACL 設定")).toBeInTheDocument();
    expect(screen.getByText("変更履歴")).toBeInTheDocument();
    expect(screen.getByText("ACL 変更履歴")).toBeInTheDocument();
    expect(screen.getByText("エクスポート(YAML)")).toBeInTheDocument();
    expect(screen.getByText("エクスポート(CSV)")).toBeInTheDocument();
    expect(screen.getByText("インポート")).toBeInTheDocument();
    expect(screen.getByText("削除アイテムの復旧")).toBeInTheDocument();
    expect(screen.getByText("削除")).toBeInTheDocument();
  });

  test("anchorElem is null, menu is closed", () => {
    const { container } = render(
      <EntityControlMenu
        entityId={1}
        anchorElem={null}
        handleClose={() => {}}
        setOpenImportModal={() => false}
      />,
      { wrapper: TestWrapper },
    );

    // menu should be closed, so menu items should not be displayed
    const menuItems = container.querySelectorAll(".MuiMenuItem-root");
    expect(menuItems.length).toBe(0);
  });

  describe("permission-based visibility", () => {
    const defaultProps = {
      entityId: 1,
      anchorElem: document.createElement("button"),
      handleClose: () => {},
      setOpenImportModal: () => false,
    };

    describe("when permission is Readable", () => {
      test("edit and import menus should not be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Readable} />,
          { wrapper: TestWrapper },
        );

        expect(screen.queryByText("編集")).not.toBeInTheDocument();
        expect(screen.queryByText("インポート")).not.toBeInTheDocument();
      });

      test("ACL and delete menus should not be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Readable} />,
          { wrapper: TestWrapper },
        );

        expect(screen.queryByText("ACL 設定")).not.toBeInTheDocument();
        expect(screen.queryByText("削除")).not.toBeInTheDocument();
      });

      test("read-only menus should still be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Readable} />,
          { wrapper: TestWrapper },
        );

        expect(screen.getByText("アイテム一覧")).toBeInTheDocument();
        expect(screen.getByText("エイリアス一覧")).toBeInTheDocument();
        expect(screen.getByText("変更履歴")).toBeInTheDocument();
        expect(screen.getByText("ACL 変更履歴")).toBeInTheDocument();
        expect(screen.getByText("エクスポート(YAML)")).toBeInTheDocument();
        expect(screen.getByText("エクスポート(CSV)")).toBeInTheDocument();
        expect(screen.getByText("削除アイテムの復旧")).toBeInTheDocument();
      });
    });

    describe("when permission is Writable", () => {
      test("edit and import menus should be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Writable} />,
          { wrapper: TestWrapper },
        );

        expect(screen.getByText("編集")).toBeInTheDocument();
        expect(screen.getByText("インポート")).toBeInTheDocument();
      });

      test("ACL and delete menus should not be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Writable} />,
          { wrapper: TestWrapper },
        );

        expect(screen.queryByText("ACL 設定")).not.toBeInTheDocument();
        expect(screen.queryByText("削除")).not.toBeInTheDocument();
      });
    });

    describe("when permission is Full", () => {
      test("all operation menus should be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Full} />,
          { wrapper: TestWrapper },
        );

        expect(screen.getByText("アイテム一覧")).toBeInTheDocument();
        expect(screen.getByText("編集")).toBeInTheDocument();
        expect(screen.getByText("ACL 設定")).toBeInTheDocument();
        expect(screen.getByText("インポート")).toBeInTheDocument();
        expect(screen.getByText("削除")).toBeInTheDocument();
      });
    });

    describe("when permission is undefined", () => {
      test("all menus should be displayed (backward compatibility)", () => {
        render(<EntityControlMenu {...defaultProps} permission={undefined} />, {
          wrapper: TestWrapper,
        });

        expect(screen.getByText("編集")).toBeInTheDocument();
        expect(screen.getByText("ACL 設定")).toBeInTheDocument();
        expect(screen.getByText("インポート")).toBeInTheDocument();
        expect(screen.getByText("削除")).toBeInTheDocument();
      });
    });
  });

  describe("delete notification", () => {
    const defaultProps = {
      entityId: 1,
      anchorElem: document.createElement("button"),
      handleClose: () => {},
      setOpenImportModal: () => false,
    };

    const buildResponseError = (status: number, body: unknown) => {
      const err = new Error("response error") as Error & {
        response: Response;
      };
      err.name = "ResponseError";
      err.response = new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      });
      return err;
    };

    afterEach(() => {
      jest.restoreAllMocks();
    });

    test("should show success snackbar on successful delete", async () => {
      jest.spyOn(aironeApiClient, "deleteEntity").mockResolvedValue(undefined);

      render(<EntityControlMenu {...defaultProps} />, {
        wrapper: TestWrapper,
      });

      fireEvent.click(screen.getByText("削除"));
      fireEvent.click(screen.getByRole("button", { name: "Yes" }));

      await waitFor(() => {
        expect(
          screen.getByText("モデルの削除が完了しました"),
        ).toBeInTheDocument();
      });
    });

    test("should show specific message when entries remain (AE-240000)", async () => {
      jest.spyOn(aironeApiClient, "deleteEntity").mockRejectedValue(
        buildResponseError(400, [
          {
            code: "AE-240000",
            message:
              "cannot delete Entity because one or more Entries are not deleted",
          },
        ]),
      );

      render(<EntityControlMenu {...defaultProps} />, {
        wrapper: TestWrapper,
      });

      fireEvent.click(screen.getByText("削除"));
      fireEvent.click(screen.getByRole("button", { name: "Yes" }));

      await waitFor(() => {
        expect(
          screen.getByText(
            /モデルの削除が失敗しました: 紐づくアイテムが残っているため削除できません。先に全てのアイテムを削除してください。/,
          ),
        ).toBeInTheDocument();
      });
    });

    test("should show backend message when response carries an unmapped code", async () => {
      jest.spyOn(aironeApiClient, "deleteEntity").mockRejectedValue(
        buildResponseError(400, [
          {
            code: "AE-999999",
            message: "something went wrong on the server side",
          },
        ]),
      );

      render(<EntityControlMenu {...defaultProps} />, {
        wrapper: TestWrapper,
      });

      fireEvent.click(screen.getByText("削除"));
      fireEvent.click(screen.getByRole("button", { name: "Yes" }));

      await waitFor(() => {
        expect(
          screen.getByText(
            /モデルの削除が失敗しました: something went wrong on the server side/,
          ),
        ).toBeInTheDocument();
      });
    });

    test("should fall back to generic message when error is not a ResponseError", async () => {
      jest
        .spyOn(aironeApiClient, "deleteEntity")
        .mockRejectedValue(new Error("network error"));

      render(<EntityControlMenu {...defaultProps} />, {
        wrapper: TestWrapper,
      });

      fireEvent.click(screen.getByText("削除"));
      fireEvent.click(screen.getByRole("button", { name: "Yes" }));

      await waitFor(() => {
        expect(
          screen.getByText("モデルの削除が失敗しました"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("export notification", () => {
    const defaultProps = {
      entityId: 1,
      anchorElem: document.createElement("button"),
      handleClose: () => {},
      setOpenImportModal: () => false,
    };

    test("should show info variant snackbar on successful export", async () => {
      jest.spyOn(aironeApiClient, "exportEntries").mockResolvedValue(undefined);

      render(<EntityControlMenu {...defaultProps} />, {
        wrapper: TestWrapper,
      });

      fireEvent.click(screen.getByText("エクスポート(YAML)"));

      await waitFor(() => {
        expect(
          screen.getByText("エクスポートのジョブ登録に成功しました"),
        ).toBeInTheDocument();
      });
    });

    test("should show error variant snackbar on failed export", async () => {
      jest
        .spyOn(aironeApiClient, "exportEntries")
        .mockRejectedValue(new Error("export failed"));

      render(<EntityControlMenu {...defaultProps} />, {
        wrapper: TestWrapper,
      });

      fireEvent.click(screen.getByText("エクスポート(CSV)"));

      await waitFor(() => {
        expect(
          screen.getByText("エクスポートのジョブ登録に失敗しました"),
        ).toBeInTheDocument();
      });
    });
  });
});
