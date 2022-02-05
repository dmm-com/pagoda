import { Box, Typography } from "@mui/material";
import React, { FC } from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath, usersPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { Loading } from "../components/common/Loading";
import { UserPasswordForm } from "../components/user/UserPasswordForm";
import { getUser } from "../utils/AironeAPIClient";
import { DjangoContext } from "../utils/DjangoContext";

export const EditUserPassword: FC = () => {
  const { userId } = useParams<{ userId: number }>();
  const djangoContext = DjangoContext.getInstance();

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

      {user.loading ? (
        <Loading />
      ) : (
        <UserPasswordForm
          user={user.value}
          asSuperuser={djangoContext.user.isSuperuser}
        />
      )}
    </Box>
  );
};
