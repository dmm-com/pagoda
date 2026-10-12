import { TriggerParent } from "@dmm-com/airone-apiclient-typescript-fetch";
import { z } from "zod";

import { translate } from "i18n/config";
import { schemaForType } from "services/ZodSchemaUtil";

export const schema = schemaForType<TriggerParent>()(
  z.object({
    id: z.number(), // Add the 'id' property
    entity: z.object({
      id: z.number().min(1, translate("trigger.form.entityRequired")),
      name: z.string(),
      isPublic: z.boolean().optional(),
      permission: z.number(),
    }),
    conditions: z
      .array(
        z.object({
          id: z.number(),
          attr: z.object({
            id: z.number().min(1, translate("trigger.form.attrRequired")),
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
          isUnmatch: z.boolean().optional(),
        }),
      )
      .min(1, translate("trigger.form.conditionsRequired")),
    actions: z
      .array(
        z.object({
          id: z.number(),
          attr: z.object({
            id: z.number().min(1, translate("trigger.form.attrRequired")),
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
      .min(1, translate("trigger.form.actionsRequired")),
  }),
);

export type Schema = z.infer<typeof schema>;
