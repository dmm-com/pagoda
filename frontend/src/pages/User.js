import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import { Link } from "react-router-dom";
import Button from "@material-ui/core/Button";
import Paper from "@material-ui/core/Paper";
import EditIcon from "@material-ui/icons/Edit";
import React, { useEffect, useState } from "react";
import { makeStyles } from "@material-ui/core/styles";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import { deleteUser, getUsers } from "../utils/AironeAPIClient";
import EditButton from "../components/common/EditButton";
import CreateButton from "../components/common/CreateButton";
import DeleteButton from "../components/common/DeleteButton";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entityName: {
    margin: theme.spacing(1),
  },
}));

export default function User({}) {
  const classes = useStyles();
  const [users, setUsers] = useState([]);
  const [updated, setUpdated] = useState(false);

  useEffect(() => {
    getUsers()
      .then((resp) => resp.json())
      .then((data) => {
        if (django_context.user.is_superuser) {
          setUsers(data);
        } else {
          setUsers(data.filter((d) => d.id === django_context.user.id));
        }
      });
    setUpdated(true);
  }, [updated]);

  const handleDelete = (event, userId) => {
    deleteUser(userId).then((_) => setUpdated(true));
  };

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

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>
                <Typography>名前</Typography>
              </TableCell>
              <TableCell>
                <Typography>メールアドレス</Typography>
              </TableCell>
              <TableCell>
                <Typography>作成日時</Typography>
              </TableCell>
              <TableCell align="right" />
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => {
              return (
                <TableRow>
                  <TableCell>
                    <Typography>{user.username}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography>{user.email}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography>{user.date_joined}</Typography>
                  </TableCell>
                  <TableCell align="right">
                    <EditButton to={`/new-ui/users/${user.id}`}>
                      編集
                    </EditButton>
                    <Button
                      variant="contained"
                      color="primary"
                      className={classes.button}
                      startIcon={<EditIcon />}
                      component={Link}
                      to={`/new-ui/users/${user.id}/password`}
                    >
                      パスワード変更
                    </Button>
                    <DeleteButton onConfirmed={(e) => handleDelete(e, user.id)}>
                      削除
                    </DeleteButton>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}
