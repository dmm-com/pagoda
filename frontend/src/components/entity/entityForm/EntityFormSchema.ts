import { z } from "zod";

import { AttributeTypes } from "../../../services/Constants";

const isObjectLikeType = (type: number): boolean => {
  return (type & AttributeTypes.object.type) !== 0;
};

const isSelectLikeType = (type: number): boolean => {
  return (type & AttributeTypes.select.type) !== 0;
};

export const schema = z.object({
  name: z.string().min(1, "モデル名は必須です").default(""),
  note: z.string().default(""),
  itemNamePattern: z
    .string()
    .default("")
    .refine(
      (value) => {
        try {
          new RegExp(value);
          return true;
        } catch {
          return false;
        }
      },
      { message: "正規表現として正しい文字列を入力してください" },
    ),
  itemNameType: z.enum(["US", "ID", "AT"]).default("US"),
  isToplevel: z.boolean().default(false),
  deleteChainExcludeEntities: z
    .array(z.object({ id: z.number(), name: z.string() }))
    .default([]),
  isolationRules: z
    .array(
      z.object({
        id: z.number().optional(),
        conditions: z
          .array(
            z.object({
              id: z.number().optional(),
              attr: z.object({
                id: z.number(),
                name: z.string(),
                type: z.number(),
              }),
              strCond: z.string().nullable().default(null),
              refCond: z
                .object({ id: z.number(), name: z.string() })
                .nullable()
                .default(null),
              boolCond: z.boolean().default(false),
              isUnmatch: z.boolean().default(false),
            }),
          )
          .min(1, "条件は1つ以上必要です"),
        action: z.object({
          id: z.number().optional(),
          isPreventAll: z.boolean().default(false),
          preventFrom: z
            .object({ id: z.number(), name: z.string() })
            .nullable()
            .default(null),
        }),
      }),
    )
    .default([]),
  webhooks: z
    .array(
      z.object({
        id: z.number().optional(),
        url: z
          .string()
          .min(1, "URLは必須です")
          .url("URLとして正しい文字列を入力してください")
          .default(""),
        label: z.string().default(""),
        isEnabled: z.boolean().default(false),
        isVerified: z.boolean().default(false).optional(),
        verificationErrorDetails: z.string().nullable().optional(),
        headers: z
          .array(
            z.object({
              headerKey: z.string().min(1, "ヘッダキーは必須です").default(""),
              headerValue: z.string().default(""),
            }),
          )
          .default([]),
      }),
    )
    .default([]),
  attrs: z
    .array(
      z
        .object({
          id: z.number().optional(),
          name: z.string().min(1, "属性名は必須です").default(""),
          type: z.number(),
          isMandatory: z.boolean().default(false),
          isDeleteInChain: z.boolean().default(false),
          isSummarized: z.boolean().default(false),
          isWritable: z.boolean().default(true),
          referral: z
            .array(
              z.object({
                id: z.number(),
                name: z.string(),
              }),
            )
            .default([]),
          note: z.string().default(""),
          defaultValue: z
            .union([z.string(), z.number(), z.boolean(), z.null()])
            .optional(),
          choices: z
            .array(
              z.object({
                // value is the backend-assigned internal id. New rows omit it;
                // existing rows keep it so the server can rename labels in place.
                value: z.string().optional(),
                label: z.string().min(1, "選択肢の表示名は必須です"),
              }),
            )
            .nullable()
            .optional(),
          choicesInUse: z.array(z.string()).optional(),
          nameOrder: z.string().default("0"),
          namePrefix: z.string().default(""),
          namePostfix: z.string().default(""),
          displayAttr: z.string().default(""),
        })
        .refine(
          (attr) => {
            // Object-like types require a referral
            if (isObjectLikeType(attr.type)) {
              return attr.referral.length > 0;
            }
            return true;
          },
          {
            message: "オブジェクト型を選択した場合、参照先は必須です",
            path: ["referral"],
          },
        )
        .refine(
          (attr) => {
            // SELECT / MULTI_SELECT require non-empty choices
            if (isSelectLikeType(attr.type)) {
              return Array.isArray(attr.choices) && attr.choices.length > 0;
            }
            return true;
          },
          {
            message: "選択肢型を選択した場合、選択肢は1つ以上必要です",
            path: ["choices"],
          },
        )
        .refine(
          (attr) => {
            // SELECT / MULTI_SELECT labels must be unique
            if (isSelectLikeType(attr.type) && Array.isArray(attr.choices)) {
              const labels = attr.choices.map((c) => c.label);
              return new Set(labels).size === labels.length;
            }
            return true;
          },
          {
            message: "選択肢の表示名は重複できません",
            path: ["choices"],
          },
        ),
    )
    .default([])
    .superRefine((attrs, ctx) => {
      const nameCounts = new Map<string, number[]>();
      attrs.forEach((attr, index) => {
        if (attr.name) {
          const indices = nameCounts.get(attr.name) || [];
          indices.push(index);
          nameCounts.set(attr.name, indices);
        }
      });
      nameCounts.forEach((indices) => {
        if (indices.length > 1) {
          indices.forEach((index) => {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: "属性名が重複しています",
              path: [index, "name"],
            });
          });
        }
      });
    }),
});

export type Schema = z.infer<typeof schema>;
