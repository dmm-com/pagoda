import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath, usersPath } from "../Routes.ts";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs.tsx";
import { UserForm } from "../components/user/UserForm.tsx";
import { getUser } from "../utils/AironeAPIClient.ts";

export function EditUser({}) {
  const { userId } = useParams();

  const user = useAsync(async () => {
    if (userId) {
      const resp = await getUser(userId);
      return await resp.json();
    }
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
        <Typography color="textPrimary">ユーザ編集</Typography>
      </AironeBreadcrumbs>

      {!user.loading && <UserForm user={user.value} />}
    </div>
  );
}
