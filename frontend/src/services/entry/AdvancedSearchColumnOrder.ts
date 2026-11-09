import { ENTRY_NAME_SORT_TARGET } from "./AdvancedSearch";

export const getAdvancedSearchColumnOrderKey = (
  entityIds: number[],
  searchAllEntities: boolean,
) =>
  `advanced_search_column_order:${searchAllEntities ? "all" : [...entityIds].sort((a, b) => a - b).join(",")}`;

export const readAdvancedSearchColumnOrder = (key: string): string[] => {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(key) ?? "[]");
    return Array.isArray(value) &&
      value.every((name) => typeof name === "string")
      ? [...new Set(value)]
      : [];
  } catch {
    return [];
  }
};

export const writeAdvancedSearchColumnOrder = (
  key: string,
  names: string[],
) => {
  try {
    localStorage.setItem(key, JSON.stringify(names));
  } catch {
    // The current page can still use its in-memory column order.
  }
};

export const orderSelectedAttributes = (
  selectedNames: string[],
  savedColumns: string[],
) => [
  ...savedColumns.filter((name) => selectedNames.includes(name)),
  ...selectedNames.filter((name) => !savedColumns.includes(name)),
];

export const keepEntryNamePosition = (
  attributeGroups: string[][],
  savedColumns: string[],
) => {
  const nameIndex = savedColumns.indexOf(ENTRY_NAME_SORT_TARGET);
  const groupsBeforeName =
    nameIndex < 0
      ? 0
      : attributeGroups.filter(
          ([baseName]) =>
            baseName != null &&
            savedColumns.indexOf(baseName) >= 0 &&
            savedColumns.indexOf(baseName) < nameIndex,
        ).length;
  return attributeGroups
    .flatMap((group, index) =>
      index === groupsBeforeName ? [ENTRY_NAME_SORT_TARGET, ...group] : group,
    )
    .concat(
      groupsBeforeName === attributeGroups.length
        ? [ENTRY_NAME_SORT_TARGET]
        : [],
    );
};
