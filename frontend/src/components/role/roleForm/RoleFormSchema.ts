import { Role } from "@dmm-com/airone-apiclient-typescript-fetch";
import { z } from "zod";

import { schemaForType } from "../../../services/ZodSchemaUtil";

type RoleForSchema = Omit<Role, "isEditable">;

export const schema = schemaForType<RoleForSchema>()(
  z
    .object({
      id: z.number().default(0),
      isActive: z.boolean().optional().default(true),
      name: z.string().min(1, { message: "ロール名は必須です" }).default(""),
      description: z.string().optional(),
      users: z
        .array(
          z.object({
            id: z.number(),
            username: z.string(),
          }),
        )
        .default([]),
      groups: z
        .array(
          z.object({
            id: z.number(),
            name: z.string(),
          }),
        )
        .default([]),
      adminUsers: z
        .array(
          z.object({
            id: z.number(),
            username: z.string(),
          }),
        )
        .default([]),
      adminGroups: z
        .array(
          z.object({
            id: z.number(),
            name: z.string(),
          }),
        )
        .default([]),
    })
    .superRefine(({ users, groups, adminUsers, adminGroups }, ctx) => {
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

      groupIds
        .flatMap((id, index) => (adminGroupIds.includes(id) ? [index] : []))
        .forEach((index) => {
          ctx.addIssue({
            path: ["groups", index], // NOTE: Nested path to feedback a concrete error info.
            code: z.ZodIssueCode.custom,
            message: "管理者と重複しているグループがあります",
          });
        });

      adminUserIds
        .flatMap((id, index) => (userIds.includes(id) ? [index] : []))
        .forEach((index) => {
          ctx.addIssue({
            path: ["adminUsers", index], // NOTE: Nested path to feedback a concrete error info.
            code: z.ZodIssueCode.custom,
            message: "メンバーとユーザーが重複しています",
          });
        });

      adminGroupIds
        .flatMap((id, index) => (groupIds.includes(id) ? [index] : []))
        .forEach((index) => {
          ctx.addIssue({
            path: ["adminGroups", index], // NOTE: Nested path to feedback a concrete error info.
            code: z.ZodIssueCode.custom,
            message: "メンバーとグループが重複しています",
          });
        });
    }),
);

export type Schema = z.infer<typeof schema>;
