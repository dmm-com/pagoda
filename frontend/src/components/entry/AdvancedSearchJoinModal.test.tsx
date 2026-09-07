/**
 */
import {
  AdvancedSearchJoinAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
  EntryAttributeTypeTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router";

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

vi.mock("hooks/usePagodaSWR", () => ({
  usePagodaSWR: () => ({ data: ["attrA", "attrB", "attrC"] }),
}));
const navigateMock = vi.hoisted(() => vi.fn());
vi.mock("react-router", async () => ({
  ...((await vi.importActual("react-router")) as object),
  useNavigate: () => navigateMock,
}));
vi.spyOn(aironeApiClient, "getEntityAttrs")
  //.mockResolvedValue(["attrA", "attrB", "attrC"]);
  .mockResolvedValue([
    { name: "attrA", id: 1, type: EntryAttributeTypeTypeEnum.STRING },
    { name: "attrB", id: 2, type: EntryAttributeTypeTypeEnum.STRING },
    { name: "attrC", id: 3, type: EntryAttributeTypeTypeEnum.STRING },
  ]);

describe("AdvancedSearchJoinModal", () => {
  test("should render modal with title and buttons", () => {
    render(
      <AdvancedSearchJoinModal
        targetEntityIds={[1]}
        searchAllEntities={false}
        targetAttrname="ref_item"
        joinAttrs={joinAttrs}
        handleClose={vi.fn()}
      />,
      { wrapper: TestWrapper },
    );
    expect(screen.getByText("結合するアイテムの属性名")).toBeInTheDocument();
    expect(screen.getByText("保存")).toBeInTheDocument();
    expect(screen.getByText("キャンセル")).toBeInTheDocument();
  });

  test("should call handleClose when clicking cancel button", () => {
    const onClose = vi.fn();
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

  test("should preserve item-name filter when adding a join", () => {
    const hintEntry = encodeURIComponent(
      JSON.stringify({ filterKey: 1, keyword: "target-item" }),
    );
    render(
      <MemoryRouter
        initialEntries={[`/ui/advanced-search-results?hint_entry=${hintEntry}`]}
      >
        <AdvancedSearchJoinModal
          targetEntityIds={[1]}
          searchAllEntities={false}
          targetAttrname="ref_item"
          joinAttrs={joinAttrs}
          handleClose={vi.fn()}
        />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByText("保存"));

    const navigation = navigateMock.mock.calls.at(-1)?.[0];
    expect(navigation.search).toContain("hint_entry=");
    expect(decodeURIComponent(navigation.search)).toContain("target-item");
  });

  test("should not render modal when targetAttrname is empty", () => {
    render(
      <AdvancedSearchJoinModal
        targetEntityIds={[1]}
        searchAllEntities={false}
        targetAttrname=""
        joinAttrs={joinAttrs}
        handleClose={vi.fn()}
      />,
      { wrapper: TestWrapper },
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
