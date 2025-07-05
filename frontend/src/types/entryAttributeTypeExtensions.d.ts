// Type extensions for auto-generated API types
// This file extends the auto-generated EntryAttributeTypeTypeEnum to include NUMBER type

import "@dmm-com/airone-apiclient-typescript-fetch";

declare module "@dmm-com/airone-apiclient-typescript-fetch" {
  export interface EntryAttributeTypeTypeEnumExtended {
    NUMBER: 256;
  }

  // Merge the extended type with the original
  export const EntryAttributeTypeTypeEnum: typeof EntryAttributeTypeTypeEnum & EntryAttributeTypeTypeEnumExtended;
}