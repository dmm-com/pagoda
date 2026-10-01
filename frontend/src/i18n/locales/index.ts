import { aclMessages } from "./acl";
import { advancedSearchMessages } from "./advancedSearch";
import { categoryMessages } from "./category";
import { commonMessages } from "./common";
import { entityMessages } from "./entity";
import { entryMessages } from "./entry";
import { entryFormMessages } from "./entryForm";
import { groupMessages } from "./group";
import { headerMessages } from "./header";
import { jobMessages } from "./job";
import { roleMessages } from "./role";
import { triggerMessages } from "./trigger";
import { userMessages } from "./user";

export const ja = {
  ...commonMessages.ja,
  ...headerMessages.ja,
  ...jobMessages.ja,
  ...entityMessages.ja,
  ...entryMessages.ja,
  ...entryFormMessages.ja,
  ...advancedSearchMessages.ja,
  ...userMessages.ja,
  ...groupMessages.ja,
  ...roleMessages.ja,
  ...aclMessages.ja,
  ...categoryMessages.ja,
  ...triggerMessages.ja,
};

export type TranslationKey = keyof typeof ja;

export const en: Record<TranslationKey, string> = {
  ...commonMessages.en,
  ...headerMessages.en,
  ...jobMessages.en,
  ...entityMessages.en,
  ...entryMessages.en,
  ...entryFormMessages.en,
  ...advancedSearchMessages.en,
  ...userMessages.en,
  ...groupMessages.en,
  ...roleMessages.en,
  ...aclMessages.en,
  ...categoryMessages.en,
  ...triggerMessages.en,
};
