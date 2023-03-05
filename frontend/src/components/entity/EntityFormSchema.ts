import { z } from "zod";

export const schema = z.object({
  name: z.string().min(1, "エンティティ名は必須です").default(""),
  note: z.string().default(""),
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
        isVerified: z.boolean().default(false),
        headers: z
          .array(
            z.object({
              headerKey: z.string().min(1, "ヘッダキーは必須です").default(""),
              headerValue: z.string().default(""),
            })
          )
          .default([]),
        isDeleted: z.boolean().default(false),
      })
    )
    .default([]),
  attrs: z
    .array(
      z.object({
        id: z.number().optional(),
        name: z.string().min(1, "属性名は必須です").default(""),
        type: z.number(),
        index: z.number(),
        isMandatory: z.boolean().default(false),
        isDeleteInChain: z.boolean().default(false),
        isSummarized: z.boolean().default(false),
        referral: z.any(), // FIXME
        isDeleted: z.boolean().default(false),
      })
    )
    .default([]),
});

export type Schema = z.infer<typeof schema>;
