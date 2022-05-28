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
