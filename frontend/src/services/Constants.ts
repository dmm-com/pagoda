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

export const UserList = {
  MAX_ROW_COUNT: 30,
};

export const JobList = {
  MAX_ROW_COUNT: 30,
};

export const EntryHistoryList = {
  MAX_ROW_COUNT: 30,
};

export const EntityHistoryList = {
  MAX_ROW_COUNT: 30,
};

export const AdvancedSerarchResultList = {
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
  array: 1 << 10,
  named: 1 << 11,
};

export const AttributeTypes: Record<string, { name: string; type: number }> = {
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
  group: {
    name: "group",
    type: BaseAttributeTypes.group,
  },
  date: {
    name: "date",
    type: BaseAttributeTypes.date,
  },
  role: {
    name: "role",
    type: BaseAttributeTypes.role,
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
};

export const JobRefreshIntervalMilliSec = 60 * 1000;

export const ACLType = {
  Nothing: 1,
  Readable: 2,
  Writable: 4,
  Full: 8,
} as const;
export type ACLType = typeof ACLType[keyof typeof ACLType];

export const ACLTypeLabels: Record<ACLType, string> = {
  [ACLType.Nothing]: "権限なし",
  [ACLType.Readable]: "閲覧",
  [ACLType.Writable]: "閲覧・編集",
  [ACLType.Full]: "閲覧・編集・削除",
};
