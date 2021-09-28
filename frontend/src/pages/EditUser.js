import React from "react";
import { Link, useParams } from "react-router-dom";
import Typography from "@material-ui/core/Typography";
import { getUser } from "../utils/AironeAPIClient";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { useAsync } from "react-use";
import { UserForm } from "../components/user/UserForm";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function EditUser({}) {
  const classes = useStyles();
  const { userId } = useParams();

  const user = useAsync(async () => {
    if (userId) {
      return getUser(userId).then((resp) => resp.json());
    }
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
        <Typography color="textPrimary">ユーザ編集</Typography>
      </AironeBreadcrumbs>

      {!user.loading && <UserForm user={user.value} />}
    </div>
  );
}
