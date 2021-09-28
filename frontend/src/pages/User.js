import Typography from "@material-ui/core/Typography";
import { Link } from "react-router-dom";
import Button from "@material-ui/core/Button";
import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { deleteUser, getUsers } from "../utils/AironeAPIClient";
import { EditButton } from "../components/common/EditButton";
import { CreateButton } from "../components/common/CreateButton";
import { DeleteButton } from "../components/common/DeleteButton";
import { UserList } from "../components/user/UserList";
import { useAsync } from "react-use";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function User({}) {
  const classes = useStyles();

  const users = useAsync(async () => {
    return getUsers()
      .then((resp) => resp.json())
      .then((data) =>
        django_context.user.is_superuser
          ? data
          : data.filter((d) => d.id === django_context.user.id)
      );
  });

  return (
    <div className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography color="textPrimary">ユーザ管理</Typography>
      </AironeBreadcrumbs>

      <div className="row">
        <div className="col">
          <div className="float-left">
            <CreateButton to={`/new-ui/users/new`}>新規作成</CreateButton>
            <Button
              className={classes.button}
              variant="outlined"
              color="secondary"
            >
              エクスポート
            </Button>
            <Button
              className={classes.button}
              variant="outlined"
              color="secondary"
              component={Link}
              to={`/new-ui/import`}
            >
              インポート
            </Button>
          </div>
          <div className="float-right"></div>
        </div>
      </div>

      {!users.loading && <UserList users={users.value} />}
    </div>
  );
}
