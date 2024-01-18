import { TriggerParent } from "@dmm-com/airone-apiclient-typescript-fetch";
import { z } from "zod";

import { schemaForType } from "services/ZodSchemaUtil";

export const schema = schemaForType<TriggerParent>()(
  z.object({
    id: z.number(), // Add the 'id' property
    entity: z.object({
      id: z.number(),
      name: z.string(),
      isPublic: z.boolean().optional(),
    }),
    conditions: z.array(
      z.object({
        id: z.number(),
        attr: z.object({
          id: z.number(),
          name: z.string(),
        }),
        strCond: z.string(),
        refCond: z.number().nullable(),
        boolCond: z.boolean().optional(),
      })
    ),
    actions: z.array(
      z.object({
        id: z.number(),
        attr: z.object({
          id: z.number(),
          name: z.string(),
        }),
        values: z.array(
          z.object({
            id: z.number(),
            strCond: z.string(),
            refCond: z.number().nullable(),
            boolCond: z.boolean().optional(),
          })
        ),
      })
    ),
  })
);

export type Schema = z.infer<typeof schema>;
