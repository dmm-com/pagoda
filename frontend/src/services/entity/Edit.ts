import { Schema } from "components/entity/entityForm/EntityFormSchema";

export const findDuplicateIndexes = (array: Schema["attrs"]): number[] => {
  const duplicateIndexes: number[] = [];
  const nameMap: Record<string, number> = {};

  array.forEach((obj, index) => {
    const name = obj.name;
    if (nameMap[name] !== undefined) {
      duplicateIndexes.push(index);
      duplicateIndexes.push(nameMap[name]);
    } else {
      nameMap[name] = index;
    }
  });

  return duplicateIndexes;
};
