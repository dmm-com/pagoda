/**
 * @jest-environment jsdom
 */

import {
  AdvancedSearchResult,
  AdvancedSearchResultValue,
  EntryAttributeTypeTypeEnum,
  EntryAttributeValue,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";

import { AttrStatsModal } from "./AttrStatsModal";

import { aironeApiClient } from "repository/AironeApiClient";

const ATTR_NAME = "Status";

const row = (
  value: EntryAttributeValue,
  isReadable = true,
  attrName = ATTR_NAME,
): AdvancedSearchResultValue =>
  ({
    attrs: {
      [attrName]: {
        type: EntryAttributeTypeTypeEnum.STRING,
        value,
        isReadable,
      },
    },
    isReadable: true,
  }) as AdvancedSearchResultValue;

const result = (
  values: AdvancedSearchResultValue[],
  totalCount = values.length,
): AdvancedSearchResult => ({
  count: values.length,
  values,
  totalCount,
});

const renderModal = (
  props: Partial<React.ComponentProps<typeof AttrStatsModal>> = {},
  initialEntry = "/ui/advanced-search?entity=10&is_all_entities=true",
) => {
  const onClose = jest.fn();
  render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AttrStatsModal
        open
        onClose={onClose}
        attrname={ATTR_NAME}
        attrType={EntryAttributeTypeTypeEnum.STRING}
        totalCount={1}
        {...props}
      />
    </MemoryRouter>,
  );
  return { onClose };
};

describe("AttrStatsModal", () => {
  let advancedSearch: jest.SpyInstance;

  beforeEach(() => {
    advancedSearch = jest.spyOn(aironeApiClient, "advancedSearch");
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test("aggregates readable values, sorts them, and forwards search params", async () => {
    advancedSearch.mockResolvedValue(
      result([
        row({ asString: "Beta" }),
        row({ asString: "Alpha" }),
        row({ asString: "Beta" }),
        row({ asString: "ignored" }, false),
        row({ asString: "other attribute" }, true, "Other"),
      ]),
    );

    renderModal({ totalCount: 5 });

    await screen.findByText("Beta");
    expect(advancedSearch).toHaveBeenCalledTimes(1);
    expect(advancedSearch).toHaveBeenCalledWith(
      [10],
      [],
      [],
      false,
      "",
      true,
      1,
      100,
      0,
      undefined,
      [],
      [],
    );

    const rows = screen.getAllByRole("row").slice(1);
    expect(rows).toHaveLength(2);
    expect(within(rows[0]).getByText("Beta")).toBeInTheDocument();
    expect(within(rows[0]).getByText("2")).toBeInTheDocument();
    expect(within(rows[1]).getByText("Alpha")).toBeInTheDocument();
    expect(screen.getByText("5 / 5 件")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  test("loads every page in sequence", async () => {
    advancedSearch
      .mockResolvedValueOnce(result([row({ asString: "First" })], 101))
      .mockResolvedValueOnce(result([row({ asString: "Second" })], 101));

    renderModal({ totalCount: 101 });

    await screen.findByText("Second");
    expect(advancedSearch).toHaveBeenCalledTimes(2);
    expect(advancedSearch.mock.calls.map((call) => call[6])).toEqual([1, 2]);
    expect(screen.getByText("101 / 101 件")).toBeInTheDocument();
  });

  test("keeps partial progress and reports a request failure", async () => {
    advancedSearch
      .mockResolvedValueOnce(result([row({ asString: "Loaded" })], 101))
      .mockRejectedValueOnce(new Error("network unavailable"));

    renderModal({ totalCount: 101 });

    expect(await screen.findByText("集計に失敗しました")).toBeInTheDocument();
    expect(screen.getByText("Loaded")).toBeInTheDocument();
    expect(screen.getByText("1 / 101 件")).toBeInTheDocument();
    expect(screen.getByText("1%")).toBeInTheDocument();
  });

  test("does not request data for a closed or empty modal", () => {
    const { rerender } = render(
      <MemoryRouter>
        <AttrStatsModal
          open={false}
          onClose={jest.fn()}
          attrname={ATTR_NAME}
          attrType={EntryAttributeTypeTypeEnum.STRING}
          totalCount={10}
        />
      </MemoryRouter>,
    );

    rerender(
      <MemoryRouter>
        <AttrStatsModal
          open
          onClose={jest.fn()}
          attrname={ATTR_NAME}
          attrType={EntryAttributeTypeTypeEnum.STRING}
          totalCount={0}
        />
      </MemoryRouter>,
    );

    expect(advancedSearch).not.toHaveBeenCalled();
    expect(screen.getByText("0 / 0 件")).toBeInTheDocument();
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  test("closes from the close button", () => {
    advancedSearch.mockResolvedValue(result([]));
    const { onClose } = renderModal({ totalCount: 0 });

    fireEvent.click(screen.getByTestId("CloseIcon"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  test.each([
    [
      EntryAttributeTypeTypeEnum.OBJECT,
      { asObject: { name: "Object" } },
      "Object",
    ],
    [EntryAttributeTypeTypeEnum.TEXT, { asString: "Text" }, "Text"],
    [EntryAttributeTypeTypeEnum.DATE, { asString: "2026-07-18" }, "2026-07-18"],
    [
      EntryAttributeTypeTypeEnum.DATETIME,
      { asString: "2026-07-18T01:02:03Z" },
      "2026-07-18T01:02:03Z",
    ],
    [EntryAttributeTypeTypeEnum.BOOLEAN, { asBoolean: false }, "false"],
    [EntryAttributeTypeTypeEnum.NUMBER, { asNumber: 42 }, "42"],
    [
      EntryAttributeTypeTypeEnum.NAMED_OBJECT,
      { asNamedObject: { name: "Alias", object: { name: "Object" } } },
      "Alias / Object",
    ],
    [EntryAttributeTypeTypeEnum.GROUP, { asGroup: { name: "Group" } }, "Group"],
    [EntryAttributeTypeTypeEnum.ROLE, { asRole: { name: "Role" } }, "Role"],
    [
      EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
      { asArrayObject: [{ name: "One" }, { name: "Two" }] },
      "One, Two",
    ],
    [
      EntryAttributeTypeTypeEnum.ARRAY_STRING,
      { asArrayString: ["One", "Two"] },
      "One, Two",
    ],
    [
      EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
      { asArrayNamedObject: [{ name: "Alias", object: { name: "Object" } }] },
      "Alias / Object",
    ],
    [
      EntryAttributeTypeTypeEnum.ARRAY_GROUP,
      { asArrayGroup: [{ name: "One" }, { name: "Two" }] },
      "One, Two",
    ],
    [
      EntryAttributeTypeTypeEnum.ARRAY_ROLE,
      { asArrayRole: [{ name: "One" }, { name: "Two" }] },
      "One, Two",
    ],
    [
      EntryAttributeTypeTypeEnum.ARRAY_NUMBER,
      { asArrayNumber: [1, null, 3] },
      "1, , 3",
    ],
    [9999, {}, "(空白)"],
  ])("formats attribute type %s", async (attrType, value, expected) => {
    advancedSearch.mockResolvedValue(
      result([row(value as unknown as EntryAttributeValue)]),
    );

    renderModal({ attrType });

    expect(await screen.findByText(expected)).toBeInTheDocument();
  });
});
