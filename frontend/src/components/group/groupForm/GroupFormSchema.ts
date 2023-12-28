import { Group } from "@dmm-com/airone-apiclient-typescript-fetch";
import { z } from "zod";

import { schemaForType } from "../../../services/ZodSchemaUtil";

export const schema = schemaForType<Group>()(
  z.object({
    id: z.number().default(0),
    name: z.string().min(1, { message: "グループ名は必須です" }),
    parentGroup: z.number().nullable().optional(),
    members: z
      .array(
        z.object({
          id: z.number(),
          username: z.string(),
        })
      )
      .default([]),
  })
);

export type Schema = z.infer<typeof schema>;
