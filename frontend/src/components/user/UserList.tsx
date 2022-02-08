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
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { Link, useHistory } from "react-router-dom";

import { passwordPath, userPath } from "Routes";
import { DeleteButton } from "components/common/DeleteButton";
import { EditButton } from "components/common/EditButton";
import { deleteUser } from "utils/AironeAPIClient";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  users: {
    id: number;
    username: string;
    email: string;
    date_joined: string;
  }[];
}

export const UserList: FC<Props> = ({ users }) => {
  const classes = useStyles();
  const history = useHistory();

  const handleDelete = (event, userId) => {
    deleteUser(userId).then(() => history.go(0));
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
};
