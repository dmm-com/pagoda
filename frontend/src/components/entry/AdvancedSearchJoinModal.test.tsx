/**
 * @jest-environment jsdom
 */
import {
  AdvancedSearchJoinAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

import { AdvancedSearchJoinModal } from "./AdvancedSearchJoinModal";

import { TestWrapper } from "TestWrapper";
import { aironeApiClient } from "repository/AironeApiClient";

const joinAttrs: AdvancedSearchJoinAttrInfo[] = [
  {
    name: "ref_item",
    attrinfo: [
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
    ],
  },
  {
    name: "other_item",
    attrinfo: [
      {
        name: "attrC",
        filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
        keyword: "",
      },
    ],
  },
];

jest.mock("hooks/useAsyncWithThrow", () => ({
  useAsyncWithThrow: () => ({ value: ["attrA", "attrB", "attrC"] }),
}));
jest.mock("react-router", () => ({
  ...jest.requireActual("react-router"),
  useNavigate: () => jest.fn(),
}));
jest
  .spyOn(aironeApiClient, "getEntityAttrs")
  .mockResolvedValue(["attrA", "attrB", "attrC"]);

describe("AdvancedSearchJoinModal", () => {
  test("should render modal with title and buttons", () => {
    render(
      <AdvancedSearchJoinModal
        targetEntityIds={[1]}
        searchAllEntities={false}
        targetAttrname="ref_item"
        joinAttrs={joinAttrs}
        handleClose={jest.fn()}
      />,
      { wrapper: TestWrapper },
    );
    expect(screen.getByText("結合するアイテムの属性名")).toBeInTheDocument();
    expect(screen.getByText("保存")).toBeInTheDocument();
    expect(screen.getByText("キャンセル")).toBeInTheDocument();
  });

  test("should call handleClose when clicking cancel button", () => {
    const onClose = jest.fn();
    render(
      <AdvancedSearchJoinModal
        targetEntityIds={[1]}
        searchAllEntities={false}
        targetAttrname="ref_item"
        joinAttrs={joinAttrs}
        handleClose={onClose}
      />,
      { wrapper: TestWrapper },
    );
    fireEvent.click(screen.getByText("キャンセル"));
    expect(onClose).toHaveBeenCalled();
  });

  test("should not render modal when targetAttrname is empty", () => {
    render(
      <AdvancedSearchJoinModal
        targetEntityIds={[1]}
        searchAllEntities={false}
        targetAttrname=""
        joinAttrs={joinAttrs}
        handleClose={jest.fn()}
      />,
      { wrapper: TestWrapper },
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
