import EditIcon from "@mui/icons-material/Edit";
import {
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import PropTypes from "prop-types";
import React from "react";
import { Link, useHistory } from "react-router-dom";

import { passwordPath, userPath } from "../../Routes";
import { deleteUser } from "../../utils/AironeAPIClient";
import { DeleteButton } from "../common/DeleteButton";
import { EditButton } from "../common/EditButton";

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
          {users.map((user) => (
            <TableRow key={user.id}>
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
                <EditButton to={userPath(user.id)}>編集</EditButton>
                <Button
                  variant="contained"
                  color="primary"
                  className={classes.button}
                  startIcon={<EditIcon />}
                  component={Link}
                  to={passwordPath(user.id)}
                >
                  パスワード変更
                </Button>
                <DeleteButton handleDelete={(e) => handleDelete(e, user.id)}>
                  削除
                </DeleteButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

UserList.propTypes = {
  users: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      username: PropTypes.string.isRequired,
      email: PropTypes.string.isRequired,
      date_joined: PropTypes.string.isRequired,
    })
  ).isRequired,
};
