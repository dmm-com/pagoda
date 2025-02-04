import { z } from "zod";

import { schemaForType } from "../../../services/ZodSchemaUtil";

import { CategoryList } from "@dmm-com/airone-apiclient-typescript-fetch";

type CategoryForSchema = Omit<CategoryList, "isEditable">;

export const schema = schemaForType<CategoryForSchema>()(
  z
    .object({
      id: z.number().default(0),
      name: z.string().min(1, { message: "カテゴリ名は必須です" }).default(""),
      note: z.string().optional(),
      models: z
        .array(
          z.object({
            id: z.number(),
            name: z.string(),
          })
        )
        .default([]),
    })
    .superRefine(({}, ctx) => {
      /*
      const userIds = users.map((u) => u.id);
      const groupIds = groups.map((g) => g.id);
      const adminUserIds = adminUsers.map((u) => u.id);
      const adminGroupIds = adminGroups.map((g) => g.id);

      if (adminUserIds.length === 0 && adminGroupIds.length === 0) {
        ctx.addIssue({
          path: ["adminUsers"],
          code: z.ZodIssueCode.custom,
          message:
            "管理者ユーザーか管理者グループのどちらかは必ずメンバーを指定してください",
        });
        ctx.addIssue({
          path: ["adminGroups"],
          code: z.ZodIssueCode.custom,
          message:
            "管理者ユーザーか管理者グループのどちらかは必ずメンバーを指定してください",
        });
      }

      userIds
        .flatMap((id, index) => (adminUserIds.includes(id) ? [index] : []))
        .forEach((index) => {
          ctx.addIssue({
            path: ["users", index], // NOTE: Nested path to feedback a concrete error info.
            code: z.ZodIssueCode.custom,
            message: "管理者と重複しているユーザーがあります",
          });
        });
        */
    })
);

export type Schema = z.infer<typeof schema>;
