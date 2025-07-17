export const EntityStatus = {
  TOP_LEVEL: 1 << 0,
  CREATING: 1 << 1,
  EDITING: 1 << 2,
};

export const EntityListParam = {
  MAX_ROW_COUNT: 30,
};

export const EntryListParam = {
  MAX_ROW_COUNT: 30,
};

export const UserListParam = {
  MAX_ROW_COUNT: 30,
};

export const JobListParam = {
  MAX_ROW_COUNT: 30,
};

export const EntryHistoryListParam = {
  MAX_ROW_COUNT: 30,
};

export const EntityHistoryListParam = {
  MAX_ROW_COUNT: 30,
};

export const AdvancedSerarchResultListParam = {
  MAX_ROW_COUNT: 100,
};

export const BaseAttributeTypes = {
  object: 1 << 0,
  string: 1 << 1,
  text: 1 << 2,
  bool: 1 << 3,
  group: 1 << 4,
  date: 1 << 5,
  role: 1 << 6,
  datetime: 1 << 7,
  number: 1 << 8,
  array: 1 << 10,
  named: 1 << 11,
};

export const AttributeTypes: Record<string, { name: string; type: number }> = {
  string: {
    name: "string",
    type: BaseAttributeTypes.string,
  },
  array_string: {
    name: "array_string",
    type: BaseAttributeTypes.string | BaseAttributeTypes.array,
  },
  object: {
    name: "object",
    type: BaseAttributeTypes.object,
  },
  array_object: {
    name: "array_object",
    type: BaseAttributeTypes.object | BaseAttributeTypes.array,
  },
  named_object: {
    name: "named_object",
    type: BaseAttributeTypes.object | BaseAttributeTypes.named,
  },
  array_named_object: {
    name: "array_named_object",
    type:
      BaseAttributeTypes.object |
      BaseAttributeTypes.named |
      BaseAttributeTypes.array,
  },
  group: {
    name: "group",
    type: BaseAttributeTypes.group,
  },
  array_group: {
    name: "array_group",
    type: BaseAttributeTypes.group | BaseAttributeTypes.array,
  },
  role: {
    name: "role",
    type: BaseAttributeTypes.role,
  },
  array_role: {
    name: "array_role",
    type: BaseAttributeTypes.role | BaseAttributeTypes.array,
  },
  text: {
    name: "textarea",
    type: BaseAttributeTypes.text,
  },
  boolean: {
    name: "boolean",
    type: BaseAttributeTypes.bool,
  },
  date: {
    name: "date",
    type: BaseAttributeTypes.date,
  },
  datetime: {
    name: "datetime",
    type: BaseAttributeTypes.datetime,
  },
  number: {
    name: "number",
    type: BaseAttributeTypes.number,
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

export const JobStatuses = {
  PREPARING: 1,
  DONE: 2,
  ERROR: 3,
  TIMEOUT: 4,
  PROCESSING: 5,
  CANCELED: 6,
};

// TODO manage it in the API side
export const JobOperations = {
  CREATE_ENTRY: 1,
  EDIT_ENTRY: 2,
  DELETE_ENTRY: 3,
  COPY_ENTRY: 4,
  IMPORT_ENTRY: 5,
  EXPORT_ENTRY: 6,
  RESTORE_ENTRY: 7,
  EXPORT_SEARCH_RESULT: 8,
  REGISTER_REFERRALS: 9,
  CREATE_ENTITY: 10,
  EDIT_ENTITY: 11,
  DELETE_ENTITY: 12,
  NOTIFY_CREATE_ENTRY: 13,
  NOTIFY_UPDATE_ENTRY: 14,
  NOTIFY_DELETE_ENTRY: 15,
  DO_COPY_ENTRY: 16,
  IMPORT_ENTRY_V2: 17,
  GROUP_REGISTER_REFERRAL: 18,
  ROLE_REGISTER_REFERRAL: 19,
  EXPORT_ENTRY_V2: 20,
  UPDATE_DOCUMENT: 21,
  EXPORT_SEARCH_RESULT_V2: 22,
  MAY_INVOKE_TRIGGER: 23,
  CREATE_ENTITY_V2: 24,
  EDIT_ENTITY_V2: 25,
  DELETE_ENTITY_V2: 26,
  CREATE_ENTRY_V2: 27,
  EDIT_ENTRY_V2: 28,
  DELETE_ENTRY_V2: 29,
};

export const JobRefreshIntervalMilliSec = 60 * 1000;

export const ACLType = {
  Nothing: 1,
  Readable: 2,
  Writable: 4,
  Full: 8,
} as const;
export type ACLType = (typeof ACLType)[keyof typeof ACLType];

export const ACLTypeLabels: Record<ACLType, string> = {
  [ACLType.Nothing]: "権限なし",
  [ACLType.Readable]: "閲覧",
  [ACLType.Writable]: "閲覧・編集",
  [ACLType.Full]: "閲覧・編集・削除",
};

export const TITLE_TEMPLATES = {
  userList: "User List",
  userEdit: "EditUser",
  groupList: "Group List",
  groupEdit: "EditGroup",
  roleList: "Role List",
  roleEdit: "EditRole",
  entryList: "Item List",
  entryDetail: "Item Detail",
  entryEdit: "EditItem",
  entityList: "Model List",
  entityEdit: "EditModel",
};
