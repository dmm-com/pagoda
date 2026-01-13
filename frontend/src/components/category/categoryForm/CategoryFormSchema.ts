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
          isPublic: z.boolean().optional(),
          permission: z.number(),
        }),
      )
      .default([]),
    priority: z.coerce.number(),
    permission: z.number().default(8),
  }),
);

export type Schema = z.infer<typeof schema>;
