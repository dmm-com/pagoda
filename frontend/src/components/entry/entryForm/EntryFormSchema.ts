import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { z } from "zod";

import { EditableEntry } from "./EditableEntry";

import { schemaForType } from "services/ZodSchemaUtil";

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
              asArrayNumber: z
                .array(
                  z.object({
                    value: z.number().nullable(),
                  }),
                )
                .optional(),
            }),
          })
          .superRefine((value, ctx) => {
            if (!value.isMandatory) {
              return;
            }

            switch (value.type) {
              case EntryAttributeTypeTypeEnum.STRING:
              case EntryAttributeTypeTypeEnum.TEXT:
              case EntryAttributeTypeTypeEnum.DATE:
              case EntryAttributeTypeTypeEnum.DATETIME:
                if (value.value.asString === "") {
                  ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "必須項目です",
                    path: ["value", "asString"],
                  });
                }
                break;
              case EntryAttributeTypeTypeEnum.ARRAY_STRING:
                if (
                  !(
                    value.value.asArrayString?.some((v) => v.value !== "") ??
                    false
                  )
                ) {
                  value.value.asArrayString?.forEach((_, index) => {
                    ctx.addIssue({
                      code: z.ZodIssueCode.custom,
                      message: "必須項目です",
                      path: ["value", "asArrayString", index, "value"],
                    });
                  });
                  if (!value.value.asArrayString?.length) {
                    ctx.addIssue({
                      code: z.ZodIssueCode.custom,
                      message: "必須項目です",
                      path: ["value", "asArrayString", 0, "value"],
                    });
                  }
                }
                break;
              case EntryAttributeTypeTypeEnum.OBJECT:
                if (value.value.asObject == null) {
                  ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "必須項目です",
                    path: ["value", "asObject"],
                  });
                }
                break;
              case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
                if (
                  !(value.value.asArrayObject?.some((v) => v != null) ?? false)
                ) {
                  ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "必須項目です",
                    path: ["value", "asArrayObject"],
                  });
                }
                break;
              case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
                if (
                  !(
                    value.value.asNamedObject?.name !== "" ||
                    value.value.asNamedObject?.object != null
                  )
                ) {
                  ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "必須項目です",
                    path: ["value", "asNamedObject", "name"],
                  });
                  ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "必須項目です",
                    path: ["value", "asNamedObject", "object"],
                  });
                }
                break;
              case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
                if (
                  !(
                    value.value.asArrayNamedObject?.some((v) => {
                      return v.name !== "" || v.object != null;
                    }) ?? false
                  )
                ) {
                  value.value.asArrayNamedObject?.forEach((_, index) => {
                    ctx.addIssue({
                      code: z.ZodIssueCode.custom,
                      message: "必須項目です",
                      path: ["value", "asArrayNamedObject", index, "name"],
                    });
                    ctx.addIssue({
                      code: z.ZodIssueCode.custom,
                      message: "必須項目です",
                      path: ["value", "asArrayNamedObject", index, "object"],
                    });
                  });
                  if (!value.value.asArrayNamedObject?.length) {
                    ctx.addIssue({
                      code: z.ZodIssueCode.custom,
                      message: "必須項目です",
                      path: ["value", "asArrayNamedObject", 0, "name"],
                    });
                    ctx.addIssue({
                      code: z.ZodIssueCode.custom,
                      message: "必須項目です",
                      path: ["value", "asArrayNamedObject", 0, "object"],
                    });
                  }
                }
                break;
              case EntryAttributeTypeTypeEnum.GROUP:
                if (value.value.asGroup == null) {
                  ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "必須項目です",
                    path: ["value", "asGroup"],
                  });
                }
                break;
              case EntryAttributeTypeTypeEnum.ARRAY_GROUP:
                if (
                  !(value.value.asArrayGroup?.some((v) => v != null) ?? false)
                ) {
                  ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "必須項目です",
                    path: ["value", "asArrayGroup"],
                  });
                }
                break;
              case EntryAttributeTypeTypeEnum.ROLE:
                if (value.value.asRole == null) {
                  ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "必須項目です",
                    path: ["value", "asRole"],
                  });
                }
                break;
              case EntryAttributeTypeTypeEnum.ARRAY_ROLE:
                if (
                  !(value.value.asArrayRole?.some((v) => v != null) ?? false)
                ) {
                  ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "必須項目です",
                    path: ["value", "asArrayRole"],
                  });
                }
                break;
              case EntryAttributeTypeTypeEnum.NUMBER:
                if (value.value.asNumber == null) {
                  ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "必須項目です",
                    path: ["value", "asNumber"],
                  });
                }
                break;
              case EntryAttributeTypeTypeEnum.ARRAY_NUMBER:
                if (
                  !(
                    value.value.asArrayNumber?.some((v) => v.value != null) ??
                    false
                  )
                ) {
                  value.value.asArrayNumber?.forEach((_, index) => {
                    ctx.addIssue({
                      code: z.ZodIssueCode.custom,
                      message: "必須項目です",
                      path: ["value", "asArrayNumber", index, "value"],
                    });
                  });
                  if (!value.value.asArrayNumber?.length) {
                    ctx.addIssue({
                      code: z.ZodIssueCode.custom,
                      message: "必須項目です",
                      path: ["value", "asArrayNumber", 0, "value"],
                    });
                  }
                }
                break;
            }
          })
          .refine(({ value, type }) => {
            switch (type) {
              case EntryAttributeTypeTypeEnum.DATE:
              case EntryAttributeTypeTypeEnum.DATETIME:
                return (
                  // check if the non-empty value is a valid date
                  (value.asString ?? "") == "" ||
                  !isNaN(new Date(value.asString ?? "").getTime())
                );
            }
            return true;
          }, "値が不正です"),
      )
      .default({}),
  }),
);

export type Schema = z.infer<typeof schema>;
