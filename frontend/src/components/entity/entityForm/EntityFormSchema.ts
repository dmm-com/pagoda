import { z } from "zod";

import { AttributeTypes } from "../../../services/Constants";

const isObjectLikeType = (type: number): boolean => {
  return (
    (type &
      (AttributeTypes.object.type |
        AttributeTypes.named_object.type |
        AttributeTypes.array_object.type |
        AttributeTypes.array_named_object.type)) !==
    0
  );
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
  isToplevel: z.boolean().default(false),
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
        ),
    )
    .default([]),
});

export type Schema = z.infer<typeof schema>;
