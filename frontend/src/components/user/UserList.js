import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import Typography from "@material-ui/core/Typography";
import EditButton from "../common/EditButton";
import Button from "@material-ui/core/Button";
import EditIcon from "@material-ui/icons/Edit";
import { Link, useHistory } from "react-router-dom";
import DeleteButton from "../common/DeleteButton";
import PropTypes from "prop-types";
import EntryList from "../entry/EntryList";
import { deleteUser } from "../../utils/AironeAPIClient";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function UserList({ users }) {
  const classes = useStyles();
  const history = useHistory();

  const handleDelete = (event, userId) => {
    deleteUser(userId).then((_) => history.go(0));
  };

  return (
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
                  <EditButton to={`/new-ui/users/${user.id}`}>編集</EditButton>
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
  );
}

EntryList.propTypes = {
  entries: PropTypes.arrayOf(
    PropTypes.objectOf({
      id: PropTypes.number.isRequired,
      username: PropTypes.string.isRequired,
      email: PropTypes.string.isRequired,
      date_joined: PropTypes.string.isRequired,
    })
  ).isRequired,
};
