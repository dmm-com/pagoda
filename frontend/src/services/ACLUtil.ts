import { translate } from "../i18n/config";

export const ACLType = {
  Nothing: 1,
  Readable: 2,
  Writable: 4,
  Full: 8,
} as const;
export type ACLType = (typeof ACLType)[keyof typeof ACLType];

// Getters resolve the label in the current language on each access.
export const ACLTypeLabels: Record<ACLType, string> = {
  get [ACLType.Nothing]() {
    return translate("acl.type.nothing");
  },
  get [ACLType.Readable]() {
    return translate("acl.type.readable");
  },
  get [ACLType.Writable]() {
    return translate("acl.type.writable");
  },
  get [ACLType.Full]() {
    return translate("acl.type.full");
  },
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
