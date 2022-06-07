export const EntityStatus = {
  TOP_LEVEL: 1 << 0,
  CREATING: 1 << 1,
  EDITING: 1 << 2,
};

export const EntityList = {
  MAX_ROW_COUNT: 30,
};

export const EntryList = {
  MAX_ROW_COUNT: 30,
};

export const BaseAttributeTypes = {
  object: 1 << 0,
  string: 1 << 1,
  text: 1 << 2,
  bool: 1 << 3,
  group: 1 << 4,
  date: 1 << 5,
  array: 1 << 10,
  named: 1 << 11,
};

export const AttributeTypes = {
  object: {
    name: "entry",
    type: BaseAttributeTypes.object,
  },
  string: {
    name: "string",
    type: BaseAttributeTypes.string,
  },
  named_object: {
    name: "named_entry",
    type: BaseAttributeTypes.object | BaseAttributeTypes.named,
  },
  array_object: {
    name: "array_entry",
    type: BaseAttributeTypes.object | BaseAttributeTypes.array,
  },
  array_string: {
    name: "array_string",
    type: BaseAttributeTypes.string | BaseAttributeTypes.array,
  },
  array_named_object: {
    name: "array_named_entry",
    type:
      BaseAttributeTypes.object |
      BaseAttributeTypes.named |
      BaseAttributeTypes.array,
  },
  array_group: {
    name: "array_group",
    type: BaseAttributeTypes.group | BaseAttributeTypes.array,
  },
  text: {
    name: "textarea",
    type: BaseAttributeTypes.text,
  },
  boolean: {
    name: "boolean",
    type: BaseAttributeTypes.bool,
  },
  group: {
    name: "group",
    type: BaseAttributeTypes.group,
  },
  date: {
    name: "date",
    type: BaseAttributeTypes.date,
  },
};

export const EntryReferralList = {
  MAX_ROW_COUNT: 30,
};

/*
 * This magic number (0xfee0) describes the distance of transferring character code.
 * When a full-width character's code is shifted this number, then that character
 * changed to half-width one with same letter at UTF-8 encoding.
 * (more detail: Type "0xfee0" to Google)
 */
export const Full2HalfWidthConstant = 0xfee0;
export const Full2HalfWidthSourceRegex = "[Ａ-Ｚａ-ｚ０-９]";
