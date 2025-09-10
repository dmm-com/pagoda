/**
 * @jest-environment jsdom
 */
import {
  AdvancedSearchResultAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
  AdvancedSearchJoinAttrInfo,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen, fireEvent } from "@testing-library/react";

import { AdvancedSearchModal } from "./AdvancedSearchModal";

import { TestWrapper } from "TestWrapper";

jest.mock("react-router", () => ({
  ...jest.requireActual("react-router"),
  useNavigate: () => jest.fn(),
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
        setOpenModal={jest.fn()}
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
    const setOpenModal = jest.fn();
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

  test("should not render modal when openModal is false", () => {
    render(
      <AdvancedSearchModal
        openModal={false}
        setOpenModal={jest.fn()}
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
