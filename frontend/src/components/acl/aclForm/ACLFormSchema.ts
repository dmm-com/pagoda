import {
  ACL,
  ACLObjtypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { z } from "zod";

import { ACLType, ACLTypeLabels } from "../../../services/Constants";
import { schemaForType } from "../../../services/ZodSchemaUtil";

/*
  "name":"20220202"
  "is_public":false,
  "default_permission":8,
  "objtype":4,
  "acl":,
  "parent":null}
*/

type ACLForm = Pick<
  ACL,
  "isPublic" | "defaultPermission" | "objtype" | "roles"
>;

export const schema = schemaForType<ACLForm>()(
  z
    .object({
      isPublic: z.boolean().optional().default(true),
      defaultPermission: z.number().optional(),
      objtype: z.nativeEnum(ACLObjtypeEnum),
      roles: z.array(
        z.object({
          id: z.number(),
          name: z.string(),
          description: z.string(),
          currentPermission: z.number(),
        }),
      ),
    })
    .superRefine(({ isPublic, defaultPermission, roles }, ctx) => {
      const isDefaultPermissionFull =
        defaultPermission != null && defaultPermission === ACLType.Full;
      const isSomeRolesFull = roles.some(
        (r) => r.currentPermission === ACLType.Full,
      );

      if (!isPublic && !isDefaultPermissionFull && !isSomeRolesFull) {
        ctx.addIssue({
          path: ["generalError"],
          code: z.ZodIssueCode.custom,
          message: `限定公開にする場合は、いずれかのロールの権限を ${
            ACLTypeLabels[ACLType.Full]
          } にしてください`,
        });
      }
    }),
);

export type Schema = z.infer<typeof schema>;
