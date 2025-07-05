import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { schemaForType } from "services/ZodSchemaUtil";
import { z } from "zod";

import { EditableEntry } from "./EditableEntry";


// Function to detect 4-byte characters (characters outside the BMP - Basic Multilingual Plane)
const hasFourByteChars = (value: string): boolean => {
  // Check for surrogate pairs (4-byte characters are represented as surrogate pairs in UTF-16)
  for (let i = 0; i < value.length; i++) {
    const code = value.charCodeAt(i);
    if (code >= 0xd800 && code <= 0xdbff) {
      // High surrogate
      if (i + 1 < value.length) {
        const nextCode = value.charCodeAt(i + 1);
        if (nextCode >= 0xdc00 && nextCode <= 0xdfff) {
          // Low surrogate - this is a 4-byte character (surrogate pair)
          return true;
        }
      }
    }
  }
  return false;
};

// A schema that's compatible with existing types
// TODO rethink it, e.g. consider to use union as a type of value
export const schema = schemaForType<EditableEntry>()(
  z.object({
    name: z
      .string()
      .trim()
      .min(1, "アイテム名は必須です")
      .max(200, "アイテム名が大きすぎます")
      .refine((value) => !hasFourByteChars(value), {
        message: "使用できない文字が含まれています",
      })
      .default(""),
    schema: z.object({
      id: z.number(),
      name: z.string(),
    }),
    attrs: z
      .record(
        z.string().min(1),
        z
          .object({
            // TODO remove these fields? it should be given by Entity
            index: z.number(),
            type: z.nativeEnum(EntryAttributeTypeTypeEnum),
            isMandatory: z.boolean().default(false),
            schema: z.object({
              id: z.number(),
              name: z.string(),
            }),
            value: z.object({
              asBoolean: z.boolean().optional(),
              asString: z
                .string()
                .max(1 << 16, "属性の値が大きすぎます")
                .refine((value) => !hasFourByteChars(value), {
                  message: "使用できない文字が含まれています",
                })
                .optional(),
              asArrayString: z
                .array(
                  z.object({
                    value: z
                      .string()
                      .max(1 << 16, "属性の値が大きすぎます")
                      .refine((value) => !hasFourByteChars(value), {
                        message: "使用できない文字が含まれています",
                      }),
                  }),
                )
                .optional(),
              asObject: z
                .object({
                  id: z.number(),
                  name: z.string().refine((value) => !hasFourByteChars(value), {
                    message: "使用できない文字が含まれています",
                  }),
                })
                .nullable()
                .optional(),
              asArrayObject: z
                .array(
                  z.object({
                    id: z.number(),
                    name: z
                      .string()
                      .refine((value) => !hasFourByteChars(value), {
                        message: "使用できない文字が含まれています",
                      }),
                  }),
                )
                .optional(),
              asNamedObject: z
                .object({
                  name: z.string().refine((value) => !hasFourByteChars(value), {
                    message: "使用できない文字が含まれています",
                  }),
                  object: z
                    .object({
                      id: z.number(),
                      name: z
                        .string()
                        .refine((value) => !hasFourByteChars(value), {
                          message: "使用できない文字が含まれています",
                        }),
                    })
                    .nullable()
                    .default(null),
                })
                .optional(),
              asArrayNamedObject: z
                .array(
                  z.object({
                    name: z
                      .string()
                      .refine((value) => !hasFourByteChars(value), {
                        message: "使用できない文字が含まれています",
                      }),
                    object: z
                      .object({
                        id: z.number(),
                        name: z
                          .string()
                          .refine((value) => !hasFourByteChars(value), {
                            message: "使用できない文字が含まれています",
                          }),
                      })
                      .nullable()
                      .default(null),
                    _boolean: z.boolean().default(false),
                  }),
                )
                .optional(),
              asGroup: z
                .object({
                  id: z.number(),
                  name: z.string().refine((value) => !hasFourByteChars(value), {
                    message: "使用できない文字が含まれています",
                  }),
                })
                .nullable()
                .optional(),
              asArrayGroup: z
                .array(
                  z.object({
                    id: z.number(),
                    name: z
                      .string()
                      .refine((value) => !hasFourByteChars(value), {
                        message: "使用できない文字が含まれています",
                      }),
                  }),
                )
                .optional(),
              asRole: z
                .object({
                  id: z.number(),
                  name: z.string().refine((value) => !hasFourByteChars(value), {
                    message: "使用できない文字が含まれています",
                  }),
                })
                .nullable()
                .optional(),
              asArrayRole: z
                .array(
                  z.object({
                    id: z.number(),
                    name: z
                      .string()
                      .refine((value) => !hasFourByteChars(value), {
                        message: "使用できない文字が含まれています",
                      }),
                  }),
                )
                .optional(),
              asNumber: z.number().nullable().optional(),
            }),
          })
          .refine(
            (value) => {
              if (!value.isMandatory) {
                return true;
              }

              switch (value.type) {
                case EntryAttributeTypeTypeEnum.STRING:
                case EntryAttributeTypeTypeEnum.TEXT:
                case EntryAttributeTypeTypeEnum.DATE:
                case EntryAttributeTypeTypeEnum.DATETIME:
                  return (value.value as any).asString !== "";
                case EntryAttributeTypeTypeEnum.ARRAY_STRING:
                  return (
                    (value.value as any).asArrayString?.some((v: any) => v.value !== "") ??
                    false
                  );
                case EntryAttributeTypeTypeEnum.OBJECT:
                  return (value.value as any).asObject != null;
                case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
                  return (
                    (value.value as any).asArrayObject?.some((v: any) => v != null) ?? false
                  );
                case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
                  return (
                    (value.value as any).asNamedObject?.name !== "" ||
                    (value.value as any).asNamedObject?.object != null
                  );
                case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
                  return (
                    (value.value as any).asArrayNamedObject?.some((v: any) => {
                      return v.name !== "" || v.object != null;
                    }) ?? false
                  );
                case EntryAttributeTypeTypeEnum.GROUP:
                  return (value.value as any).asGroup != null;
                case EntryAttributeTypeTypeEnum.ARRAY_GROUP:
                  return (
                    (value.value as any).asArrayGroup?.some((v: any) => v != null) ?? false
                  );
                case EntryAttributeTypeTypeEnum.ROLE:
                  return (value.value as any).asRole != null;
                case EntryAttributeTypeTypeEnum.ARRAY_ROLE:
                  return (
                    (value.value as any).asArrayRole?.some((v: any) => v != null) ?? false
                  );
                case EntryAttributeTypeTypeEnum.NUMBER:
                  return (value.value as any).asNumber != null;
              }

              return true;
            },
            // TODO specify path to feedback users error cause
            "必須項目です",
          )
          .refine(({ value, type }) => {
            switch (type) {
              case EntryAttributeTypeTypeEnum.DATE:
              case EntryAttributeTypeTypeEnum.DATETIME:
                return (
                  // check if the non-empty value is a valid date
                  ((value as any).asString ?? "") == "" ||
                  !isNaN(new Date((value as any).asString ?? "").getTime())
                );
            }
            return true;
          }, "値が不正です"),
      )
      .default({}),
  }),
);

export type Schema = z.infer<typeof schema>;
