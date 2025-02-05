import { CategoryList } from "@dmm-com/airone-apiclient-typescript-fetch";
import { z } from "zod";

import { schemaForType } from "services/ZodSchemaUtil";

export const schema = schemaForType<CategoryList>()(
  z.object({
    id: z.number().default(0),
    name: z.string().min(1, { message: "カテゴリ名は必須です" }).default(""),
    note: z.string().optional(),
    models: z
      .array(
        z.object({
          id: z.number(),
          name: z.string(),
        })
      )
      .default([]),
  })
);

export type Schema = z.infer<typeof schema>;
