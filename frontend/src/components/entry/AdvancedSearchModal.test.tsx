/**
 */
import {
  AdvancedSearchResultAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
  AdvancedSearchJoinAttrInfo,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, render, screen, fireEvent } from "@testing-library/react";

import { AdvancedSearchModal } from "./AdvancedSearchModal";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

vi.mock("react-router", async () => ({
  ...((await vi.importActual("react-router")) as object),
  useNavigate: () => vi.fn(),
}));

describe("AdvancedSearchModal", () => {
  const attrNames = ["attrA", "attrB", "attrC"];
  const initialAttrNames = ["attrA", "attrC"];
  const attrInfos: AdvancedSearchResultAttrInfo[] = [
    {
      name: "attrA",
      filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
      keyword: "",
    },
    {
      name: "attrB",
      filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
      keyword: "",
    },
    {
      name: "attrC",
      filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
      keyword: "",
    },
  ];
  const joinAttrs: AdvancedSearchJoinAttrInfo[] = [];

  test("should render modal with title, buttons, and checkbox", () => {
    render(
      <AdvancedSearchModal
        openModal={true}
        setOpenModal={vi.fn()}
        attrNames={attrNames}
        initialAttrNames={initialAttrNames}
        attrInfos={attrInfos}
        joinAttrs={joinAttrs}
      />,
      { wrapper: TestWrapper },
    );
    expect(screen.getByText("検索属性の再設定")).toBeInTheDocument();
    expect(screen.getByText("保存")).toBeInTheDocument();
    expect(screen.getByText("キャンセル")).toBeInTheDocument();
    expect(screen.getByText("参照アイテムも含める")).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeInTheDocument();
  });

  test("should call setOpenModal(false) when clicking cancel button", () => {
    const setOpenModal = vi.fn();
    render(
      <AdvancedSearchModal
        openModal={true}
        setOpenModal={setOpenModal}
        attrNames={attrNames}
        initialAttrNames={initialAttrNames}
        attrInfos={attrInfos}
        joinAttrs={joinAttrs}
      />,
      { wrapper: TestWrapper },
    );
    fireEvent.click(screen.getByText("キャンセル"));
    expect(setOpenModal).toHaveBeenCalledWith(false);
  });

  test("renders in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });
    render(
      <AdvancedSearchModal
        openModal={true}
        setOpenModal={vi.fn()}
        attrNames={attrNames}
        initialAttrNames={initialAttrNames}
        attrInfos={attrInfos}
        joinAttrs={joinAttrs}
      />,
      { wrapper: TestWrapper },
    );
    expect(screen.getByText("Reset search attributes")).toBeInTheDocument();
    expect(screen.getByText("Save")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
    expect(screen.getByText("Include referral entries")).toBeInTheDocument();
  });

  test("should not render modal when openModal is false", () => {
    render(
      <AdvancedSearchModal
        openModal={false}
        setOpenModal={vi.fn()}
        attrNames={attrNames}
        initialAttrNames={initialAttrNames}
        attrInfos={attrInfos}
        joinAttrs={joinAttrs}
      />,
      { wrapper: TestWrapper },
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
