import { z } from "zod";

import { TriggerParent } from "@dmm-com/airone-apiclient-typescript-fetch";
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
          type: z.number(),
        }),
        strCond: z.string().nullable(),
        refCond: z.object({
          id: z.number(),
          name: z.string(),
          schema: z.object({
            id: z.number(),
            name: z.string(),
          }),
        }).nullable(),
        boolCond: z.boolean().optional(),
      })
    ),
    actions: z.array(
      z.object({
        id: z.number(),
        attr: z.object({
          id: z.number(),
          name: z.string(),
          type: z.number(),
        }),
        values: z.array(z.object({
          id: z.number(),
          strCond: z.string().nullable(),
          refCond: z.object({
            id: z.number(),
            name: z.string(),
            schema: z.object({
              id: z.number(),
              name: z.string(),
            }),
          }).nullable(),
          boolCond: z.boolean().optional(),
        })),
      })
    ),
  })
);

export type Schema = z.infer<typeof schema>;