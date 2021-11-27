import Typography from "@material-ui/core/Typography";
import React, { FC } from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath, usersPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { UserPasswordForm } from "../components/user/UserPasswordForm";
import { getUser } from "../utils/AironeAPIClient";

export const EditUserPassword: FC = () => {
  const { userId } = useParams<{ userId: number }>();

  const user = useAsync(async () => {
    const resp = await getUser(userId);
    return await resp.json();
  });

  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={usersPath()}>
          ユーザ管理
        </Typography>
        <Typography color="textPrimary">パスワード編集</Typography>
      </AironeBreadcrumbs>

      {!user.loading && (
        <UserPasswordForm
          user={user.value}
          asSuperuser={(window as any).django_context.user.is_superuser}
        />
      )}
    </div>
  );
};
