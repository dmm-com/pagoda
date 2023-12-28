import { z } from "zod";

import { TriggerParentCreate } from "@dmm-com/airone-apiclient-typescript-fetch";
import { schemaForType } from "services/ZodSchemaUtil";

export const schema = schemaForType<TriggerParentCreate>()(
  z.object({
    id: z.number(), // Add the 'id' property
    entityId: z.number(),
    conditions: z.array(
      z.object({
        attrId: z.number(),
        cond: z.string(),
      })
    ),
    actions: z.array(
      z.object({
        attrId: z.number(),
        value: z.string().optional(),
        values: z.array(z.string()).optional(),
      })
    ),
  })
);

export type Schema = z.infer<typeof schema>;
