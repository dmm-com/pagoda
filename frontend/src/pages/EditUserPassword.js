import React from "react";
import { Link, useParams } from "react-router-dom";
import Typography from "@material-ui/core/Typography";
import { getUser } from "../utils/AironeAPIClient";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import { useAsync } from "react-use";
import { UserPasswordForm } from "../components/user/UserPasswordForm";

export default function EditUserPassword({}) {
  const { userId } = useParams();

  const user = useAsync(async () => {
    return getUser(userId)
      .then((resp) => resp.json())
      .then((data) => data);
  });

  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography component={Link} to="/new-ui/users">
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
    </div>
  );
}
