import { UserRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import { z } from "zod";

import { schemaForType } from "../../../services/ZodSchemaUtil";

interface User
  extends Pick<UserRetrieve, "username" | "email" | "isSuperuser"> {
  password?: string;
}

export const schema = schemaForType<User>()(
  z.object({
    username: z.string().min(1, { message: "ユーザ名は必須です" }),
    email: z
      .string()
      .email("正しいメールアドレスを入力してください")
      .optional(),
    isSuperuser: z.boolean().default(false),
    password: z.string().min(1, { message: "パスワードは必須です" }).optional(),
  }),
);

export type Schema = z.infer<typeof schema>;
