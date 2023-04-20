import { z } from "zod";

import { schemaForType } from "../../../services/ZodSchemaUtil";

import { EditableEntry } from "./EditableEntry";

// A schema that's compatible with existing types
// TODO rethink it, e.g. consider to use union as a type of value
export const schema = schemaForType<EditableEntry>()(
  z.object({
    name: z.string().min(1, "エントリ名は必須です").default(""),
    schema: z.object({
      id: z.number(),
      name: z.string(),
    }),
    attrs: z
      .record(
        z.string().min(1),
        z.object({
          // TODO remove these fields? it should be given by Entity
          type: z.number(),
          isMandatory: z.boolean().default(false),
          schema: z.object({
            id: z.number(),
            name: z.string(),
          }),
          value: z.object({
            asBoolean: z.boolean().optional(),
            asString: z.string().optional(),
            asArrayString: z.array(z.string()).default([""]).optional(),
            asObject: z
              .object({
                id: z.number(),
                name: z.string(),
                _boolean: z.boolean().default(false),
              })
              .optional(),
            asArrayObject: z
              .array(
                z.object({
                  id: z.number(),
                  name: z.string(),
                  _boolean: z.boolean().default(false),
                })
              )
              .optional(),
            asNamedObject: z
              .record(
                z.string().min(1),
                z
                  .object({
                    id: z.number(),
                    name: z.string(),
                    _boolean: z.boolean().default(false),
                  })
                  .nullable()
                  .default(null)
              )
              .optional(),
            asArrayNamedObject: z
              .array(
                z.record(
                  z.string().min(1),
                  z
                    .object({
                      id: z.number(),
                      name: z.string(),
                      _boolean: z.boolean().default(false),
                    })
                    .nullable()
                    .default(null)
                )
              )
              .optional(),
            asGroup: z
              .object({
                id: z.number(),
                name: z.string(),
              })
              .nullable()
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
              .nullable()
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
