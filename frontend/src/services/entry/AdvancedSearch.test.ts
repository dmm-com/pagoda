import { AdvancedSearchResultAttrInfoFilterKeyEnum } from "@dmm-com/airone-apiclient-typescript-fetch";

import {
  extractAdvancedSearchParams,
  formatAdvancedSearchParams,
} from "./AdvancedSearch";

describe("formatAdvancedSearchParams", () => {
  const baseParams = (() => {
    const params = new URLSearchParams();

    params.append("entity", "101");
    params.append("entity", "102");
    params.set("is_all_entities", "false");
    params.set("has_referral", "false");
    params.set("referral_name", "hoge");
    params.set(
      "attrinfo",
      JSON.stringify([
        {
          name: "hoge",
          filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
          keyword: "",
        },
      ]),
    );

    return params;
  })();

  test("set params", () => {
    const actual = formatAdvancedSearchParams({
      entityIds: ["1", "2"],
      searchAllEntities: true,
      hasReferral: true,
      referralName: "referral_name",
      attrsFilter: {
        attr1: {
          filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
          keyword: "",
        },
      },
      hintEntry: {
        filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
        keyword: "test-hint",
      },
    });

    expect(actual.getAll("entity")).toEqual(["1", "2"]);
    expect(actual.get("is_all_entities")).toBe("true");
    expect(actual.get("has_referral")).toBe("true");
    expect(actual.get("referral_name")).toBe("referral_name");
    expect(actual.get("attrinfo")).toBe(
      JSON.stringify([
        {
          name: "attr1",
          filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
          keyword: "",
        },
      ]),
    );
    expect(actual.get("hint_entry")).toBe(
      JSON.stringify({ filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED, keyword: "test-hint" })
    );
  });

  test("set specified params partially", () => {
    const actual = formatAdvancedSearchParams({
      entityIds: ["1", "2"],
    });

    expect(actual.getAll("entity").map((e) => Number(e))).toEqual([1, 2]);
  });

  test("overwrite base params", () => {
    const actual = formatAdvancedSearchParams({
      entityIds: ["1", "2"],
      baseParams,
    });

    // overwritten
    expect(actual.getAll("entity").map((e) => Number(e))).toEqual([1, 2]);
    // base params
    expect(actual.get("is_all_entities")).toEqual("false");
    expect(actual.get("has_referral")).toEqual("false");
    expect(actual.get("referral_name")).toEqual("hoge");
    expect(actual.get("attrinfo")).toEqual(
      JSON.stringify([
        {
          name: "hoge",
          filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
          keyword: "",
        },
      ]),
    );
  });
});

describe("extractAdvancedSearchParams", () => {
  const baseParams = (() => {
    const params = new URLSearchParams();

    params.append("entity", "1");
    params.append("entity", "2");
    params.set("is_all_entities", "true");
    params.set("has_referral", "true");
    params.set("referral_name", "referral_name");
    params.set(
      "attrinfo",
      JSON.stringify([
        {
          name: "attr1",
          filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
          keyword: "",
        },
      ]),
    );

    return params;
  })();

  test("extract set params", () => {
    const {
      entityIds,
      searchAllEntities,
      hasReferral,
      referralName,
      attrInfo,
    } = extractAdvancedSearchParams(baseParams);

    expect(entityIds).toEqual([1, 2]);
    expect(searchAllEntities).toEqual(true);
    expect(hasReferral).toEqual(true);
    expect(referralName).toEqual("referral_name");
    expect(attrInfo).toEqual([
      {
        name: "attr1",
        filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
        keyword: "",
      },
    ]);
  });

  test("extract default params", () => {
    const {
      entityIds,
      searchAllEntities,
      hasReferral,
      referralName,
      attrInfo,
    } = extractAdvancedSearchParams(new URLSearchParams());

    expect(entityIds).toEqual([]);
    expect(searchAllEntities).toEqual(false);
    expect(hasReferral).toEqual(false);
    expect(referralName).toEqual("");
    expect(attrInfo).toEqual([]);
  });

  test("extractAdvancedSearchParams with hint_entry", () => {
    const params = new URLSearchParams();
    params.set("hint_entry", JSON.stringify({ filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY, keyword: "hint-keyword" }));
    const extracted = extractAdvancedSearchParams(params);
    expect(extracted.hintEntry).toEqual({ filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY, keyword: "hint-keyword" });
  });
});
