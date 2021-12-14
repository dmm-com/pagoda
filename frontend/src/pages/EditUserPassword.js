import { Box } from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath, usersPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { UserPasswordForm } from "../components/user/UserPasswordForm";
import { getUser } from "../utils/AironeAPIClient";

export function EditUserPassword({}) {
  const { userId } = useParams();

  const user = useAsync(async () => {
    const resp = await getUser(userId);
    return await resp.json();
  });

  return (
    <Box>
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
          asSuperuser={django_context.user.is_superuser}
        />
      )}
    </Box>
  );
}
