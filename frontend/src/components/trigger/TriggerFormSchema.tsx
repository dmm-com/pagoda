import { TriggerParent } from "@dmm-com/airone-apiclient-typescript-fetch";
import { z } from "zod";

import { schemaForType } from "services/ZodSchemaUtil";

export const schema = schemaForType<TriggerParent>()(
  z.object({
    id: z.number(), // Add the 'id' property
    entity: z.object({
      id: z.number().min(1, "モデルは必須です"),
      name: z.string(),
      isPublic: z.boolean().optional(),
    }),
    conditions: z
      .array(
        z.object({
          id: z.number(),
          attr: z.object({
            id: z.number().min(1, "属性は必須です"),
            name: z.string(),
            type: z.number(),
          }),
          strCond: z.string().nullable(),
          refCond: z
            .object({
              id: z.number(),
              name: z.string(),
              schema: z.object({
                id: z.number(),
                name: z.string(),
              }),
            })
            .nullable(),
          boolCond: z.boolean().optional(),
        }),
      )
      .min(1, "最低でもひとつの条件を設定してください"),
    actions: z
      .array(
        z.object({
          id: z.number(),
          attr: z.object({
            id: z.number().min(1, "属性は必須です"),
            name: z.string(),
            type: z.number(),
          }),
          values: z.array(
            z.object({
              id: z.number(),
              strCond: z.string().nullable(),
              refCond: z
                .object({
                  id: z.number(),
                  name: z.string(),
                  schema: z.object({
                    id: z.number(),
                    name: z.string(),
                  }),
                })
                .nullable(),
              boolCond: z.boolean().optional(),
            }),
          ),
        }),
      )
      .min(1, "最低でもひとつのアクションを設定してください"),
  }),
);

export type Schema = z.infer<typeof schema>;
