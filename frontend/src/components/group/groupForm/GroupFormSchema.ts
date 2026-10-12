import { Group } from "@dmm-com/airone-apiclient-typescript-fetch";
import { z } from "zod";

import { translate } from "../../../i18n/config";
import { schemaForType } from "../../../services/ZodSchemaUtil";

export const schema = schemaForType<Group>()(
  z.object({
    id: z.number().default(0),
    name: z.string().min(1, { message: translate("group.form.nameRequired") }),
    parentGroup: z.number().nullable().optional(),
    members: z
      .array(
        z.object({
          id: z.number(),
          username: z.string(),
        }),
      )
      .default([]),
  }),
);

export type Schema = z.infer<typeof schema>;
