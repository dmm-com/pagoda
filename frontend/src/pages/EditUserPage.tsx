import { Box, Typography } from "@mui/material";
import React, { FC } from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath, usersPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { UserForm } from "components/user/UserForm";
import { getUser } from "utils/AironeAPIClient";

export const EditUserPage: FC = () => {
  const { userId } = useParams<{ userId: number }>();

  const user = useAsync(async () => {
    if (userId) {
      const resp = await getUser(userId);
      return await resp.json();
    }
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
        <Typography color="textPrimary">ユーザ編集</Typography>
      </AironeBreadcrumbs>

      {user.loading ? <Loading /> : <UserForm user={user.value} />}
    </Box>
  );
};
