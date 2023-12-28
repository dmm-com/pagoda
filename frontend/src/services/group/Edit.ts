import { GroupTree } from "../../repository/AironeApiClientV2";

export const filterAncestorsAndOthers = (
  groupTrees: GroupTree[],
  targetGroupId: number
): GroupTree[] => {
  return groupTrees
    .filter((t) => t.id !== targetGroupId)
    .map((t) => ({
      ...t,
      children: filterAncestorsAndOthers(t.children, targetGroupId),
    }));
};
