import { z } from "zod";

import { schemaForType } from "../../services/ZodSchemaUtil";

import { EditableEntry } from "./entryForm/EditableEntry";

// A schema that's compatible with existing types
// TODO rethink it, e.g. consider to use union as a type of value
export const schema = schemaForType<EditableEntry>()(
  z.object({
    name: z.string().min(1, "エントリ名は必須です").default(""),
    attrs: z
      .record(
        z.string().min(1),
        z.object({
          id: z.number().nullable(),
          type: z.number(),
          isMandatory: z.boolean().default(false),
          schema: z.object({
            id: z.number(),
            name: z.string(),
          }),
          value: z.object({
            asBoolean: z.boolean().optional(),
            asString: z.string().optional(),
            asArrayString: z.array(z.string()).optional(),
            asObject: z
              .object({
                id: z.number(),
                name: z.string(),
                schema: z.object({
                  id: z.number(),
                  name: z.string(),
                }),
                _boolean: z.boolean(),
              })
              .optional(),
            asArrayObject: z
              .array(
                z.object({
                  id: z.number(),
                  name: z.string(),
                  schema: z.object({
                    id: z.number(),
                    name: z.string(),
                  }),
                  _boolean: z.boolean(),
                })
              )
              .optional(),
            asNamedObject: z.record(
              z.string().min(1),
              z.object({
                id: z.number(),
                name: z.string(),
                schema: z.object({
                  id: z.number(),
                  name: z.string(),
                }),
                _boolean: z.boolean(),
              })
            ),
            asArrayNamedObject: z.array(
              z.record(
                z.string(),
                z.object({
                  id: z.number(),
                  name: z.string(),
                  schema: z.object({
                    id: z.number(),
                    name: z.string(),
                  }),
                  _boolean: z.boolean(),
                })
              )
            ),
            asGroup: z
              .object({
                id: z.number(),
                name: z.string(),
              })
              .optional(),
            asArrayGroup: z
              .array(
                z.object({
                  id: z.number(),
                  name: z.string(),
                })
              )
              .optional(),
            asRole: z
              .object({
                id: z.number(),
                name: z.string(),
              })
              .optional(),
            asArrayRole: z
              .array(
                z.object({
                  id: z.number(),
                  name: z.string(),
                })
              )
              .optional(),
          }),
        })
      )
      .default({}),
  })
);

export type Schema = z.infer<typeof schema>;
