import {
  AdvancedSearchJoinAttrInfo,
  AdvancedSearchResultAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
  EntryHint,
} from "@dmm-com/airone-apiclient-typescript-fetch";

export type AttrFilter = {
  filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum;
  keyword: string;
  baseAttrname?: string;
  joinedAttrname?: string;
};

export type AttrsFilter = Record<string, AttrFilter>;

export type JoinAttr = {
  name: string;
  attrinfo: AdvancedSearchResultAttrInfo[];
};

export interface AdvancedSearchParams {
  entityIds: number[];
  searchAllEntities: boolean;
  hasReferral: boolean;
  referralName: string;
  attrInfo: AdvancedSearchResultAttrInfo[];
  joinAttrs: AdvancedSearchJoinAttrInfo[];
  hintEntry?: EntryHint;
}

const AdvancedSearchParamKey = {
  ENTITY_IDS: "entity",
  SEARCH_ALL_ENTITIES: "is_all_entities",
  HAS_REFERRAL: "has_referral",
  REFERRAL_NAME: "referral_name",
  ATTR_INFO: "attrinfo",
  PAGE: "page",
  JOIN_ATTRS: "join_attrs",
  HINT_ENTRY: "hint_entry",
} as const;
type AdvancedSearchParamKey =
  (typeof AdvancedSearchParamKey)[keyof typeof AdvancedSearchParamKey];

/**
 * A wrapper around URLSearchParams that provides a keyname-safe interface for advanced search
 */
class AdvancedSearchParamsInner {
  private params: URLSearchParams;

  constructor(params: URLSearchParams) {
    this.params = params;
  }

  get(key: AdvancedSearchParamKey): string | null {
    return this.params.get(key);
  }

  getAll(key: AdvancedSearchParamKey): string[] | null {
    return this.params.getAll(key);
  }

  set(key: AdvancedSearchParamKey, value: string): void {
    return this.params.set(key, value);
  }

  append(key: AdvancedSearchParamKey, value: string): void {
    return this.params.append(key, value);
  }

  delete(key: AdvancedSearchParamKey): void {
    return this.params.delete(key);
  }

  urlSearchParams(): URLSearchParams {
    return this.params;
  }
}

export function formatAdvancedSearchParams({
  attrsFilter,
  entityIds,
  searchAllEntities,
  hasReferral,
  referralName,
  baseParams,
  joinAttrs,
  hintEntry,
}: {
  attrsFilter?: AttrsFilter;
  entityIds?: string[];
  searchAllEntities?: boolean;
  hasReferral?: boolean;
  referralName?: string;
  baseParams?: URLSearchParams;
  joinAttrs?: JoinAttr[];
  hintEntry?: EntryHint;
}): URLSearchParams {
  const params = new AdvancedSearchParamsInner(new URLSearchParams(baseParams));

  if (entityIds != null) {
    params.delete("entity");
    entityIds.forEach((id) => {
      params.append("entity", id);
    });
  }

  if (searchAllEntities != null) {
    params.set("is_all_entities", String(searchAllEntities));
  }

  if (hasReferral != null) {
    params.set("has_referral", String(hasReferral));
  }

  if (referralName != null) {
    params.set("referral_name", referralName);
  }

  if (attrsFilter != null) {
    params.set(
      "attrinfo",
      JSON.stringify(
        Object.keys(attrsFilter).map(
          (key): AdvancedSearchResultAttrInfo => ({
            name: key,
            filterKey: attrsFilter[key].filterKey,
            keyword: attrsFilter[key].keyword,
          }),
        ),
      ),
    );
  }

  if (joinAttrs != null) {
    params.delete("join_attrs");
    joinAttrs.forEach((joinAttr) => {
      if (joinAttr.attrinfo.length > 0) {
        params.append("join_attrs", JSON.stringify(joinAttr));
      }
    });
  }

  if (hintEntry != null) {
    params.set(AdvancedSearchParamKey.HINT_ENTRY, JSON.stringify(hintEntry));
  } else {
    params.delete(AdvancedSearchParamKey.HINT_ENTRY);
  }

  params.delete("page");

  return params.urlSearchParams();
}

export function extractAdvancedSearchParams(
  baseParams: URLSearchParams,
): AdvancedSearchParams {
  const params = new AdvancedSearchParamsInner(baseParams);

  const entityIds = params.getAll("entity")?.map((id) => Number(id)) ?? [];
  const searchAllEntities = params.get("is_all_entities") === "true";
  const hasReferral = params.get("has_referral") === "true";
  const referralName = params.get("referral_name") ?? "";
  const attrInfo: AdvancedSearchResultAttrInfo[] = JSON.parse(
    params.get("attrinfo") ?? "[]",
  );
  const joinAttrs: AdvancedSearchJoinAttrInfo[] =
    params.getAll("join_attrs")?.map((x) => JSON.parse(x)) ?? [];

  let hintEntry: EntryHint | undefined = undefined;
  const hintEntryRaw = params.get("hint_entry");
  if (hintEntryRaw) {
    hintEntry = JSON.parse(hintEntryRaw) as EntryHint;
  }

  return {
    entityIds,
    searchAllEntities,
    hasReferral,
    referralName,
    attrInfo,
    joinAttrs,
    hintEntry,
  };
}
