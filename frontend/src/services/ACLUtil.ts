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

/**
 * Check if user can edit the object (requires Writable or higher permission).
 */
export const canEdit = (permission: number): boolean =>
  permission >= ACLType.Writable;

/**
 * Check if user can modify ACL settings (requires Full permission).
 */
export const canModifyACL = (permission: number): boolean =>
  permission >= ACLType.Full;
