import {
  AdvancedSearchResultAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";

export type AttrFilter = {
  filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum;
  keyword: string;
};

export type AttrsFilter = Record<string, AttrFilter>;

interface AdvancedSearchParams {
  entityIds: number[];
  searchAllEntities: boolean;
  entryName: string;
  hasReferral: boolean;
  referralName: string;
  attrInfo: AdvancedSearchResultAttrInfo[];
}

const AdvancedSearchParamKey = {
  ENTITY_IDS: "entity",
  SEARCH_ALL_ENTITIES: "is_all_entities",
  ENTRY_NAME: "entry_name",
  HAS_REFERRAL: "has_referral",
  REFERRAL_NAME: "referral_name",
  ATTR_INFO: "attrinfo",
  PAGE: "page",
} as const;
type AdvancedSearchParamKey =
  typeof AdvancedSearchParamKey[keyof typeof AdvancedSearchParamKey];

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
  entryName,
  hasReferral,
  referralName,
  baseParams,
}: {
  attrsFilter?: AttrsFilter;
  entityIds?: string[];
  searchAllEntities?: boolean;
  entryName?: string;
  hasReferral?: boolean;
  referralName?: string;
  baseParams?: URLSearchParams;
}): URLSearchParams {
  const params = new AdvancedSearchParamsInner(new URLSearchParams(baseParams));

  if (entityIds != null) {
    params.delete("entity");
    entityIds.forEach((id) => {
      params.append("entity", id);
    });
  }

  if (entryName != null) {
    params.set("entry_name", entryName);
  }

  if (searchAllEntities != null) {
    params.set("is_all_entities", searchAllEntities ? "true" : "false");
  }

  if (hasReferral != null) {
    params.set("has_referral", hasReferral ? "true" : "false");
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
          })
        )
      )
    );
  }

  params.delete("page");

  return params.urlSearchParams();
}

export function extractAdvancedSearchParams(
  baseParams: URLSearchParams
): AdvancedSearchParams {
  const params = new AdvancedSearchParamsInner(baseParams);

  const entityIds = params.getAll("entity")?.map((id) => Number(id)) ?? [];
  const searchAllEntities = params.get("is_all_entities") === "true";
  const entryName = params.get("entry_name") ?? "";
  const hasReferral = params.get("has_referral") === "true";
  const referralName = params.get("referral_name") ?? "";
  const attrInfo: AdvancedSearchResultAttrInfo[] = JSON.parse(
    params.get("attrinfo") ?? "[]"
  );

  return {
    entityIds,
    searchAllEntities,
    entryName,
    hasReferral,
    referralName,
    attrInfo,
  };
}
