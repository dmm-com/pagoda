import { UserRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import { z } from "zod";

import { translate } from "../../../i18n/config";
import { schemaForType } from "../../../services/ZodSchemaUtil";

interface User
  extends Pick<UserRetrieve, "username" | "email" | "isSuperuser"> {
  password?: string;
  tokenLifetime?: number;
}

export const schema = schemaForType<User>()(
  z.object({
    username: z
      .string()
      .min(1, { message: translate("user.form.usernameRequired") }),
    email: z.string().email(translate("user.form.emailInvalid")).optional(),
    isSuperuser: z.boolean().default(false),
    password: z
      .string()
      .min(1, { message: translate("user.form.passwordRequired") })
      .optional(),
    tokenLifetime: z.coerce
      .number({
        invalid_type_error: translate("user.form.tokenLifetimeInvalid"),
      })
      .int(translate("user.form.tokenLifetimeNotInteger"))
      .min(0, { message: translate("user.form.tokenLifetimeMin") })
      .optional(),
  }),
);

export type Schema = z.infer<typeof schema>;
