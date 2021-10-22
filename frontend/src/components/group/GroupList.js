import {
  List,
  ListItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import Typography from "@material-ui/core/Typography";
import PropTypes from "prop-types";
import React from "react";
import { Link, useHistory } from "react-router-dom";

import { groupPath } from "../../Routes";
import { deleteGroup } from "../../utils/AironeAPIClient";
import { DeleteButton } from "../common/DeleteButton";

export function GroupList({ groups }) {
  const history = useHistory();

  const handleDelete = (event, groupId) => {
    deleteGroup(groupId).then(() => history.go(0));
  };

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>
              <Typography>名前</Typography>
            </TableCell>
            <TableCell align="right">
              <Typography align="left">メンバー</Typography>
            </TableCell>
            <TableCell align="right" />
          </TableRow>
        </TableHead>
        <TableBody>
          {groups.map((group) => (
            <TableRow key={group.id}>
              <TableCell>
                <Typography component={Link} to={groupPath(group.id)}>
                  {group.name}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <List>
                  {group.members.map((member) => (
                    <ListItem key={member.id}>{member.username}</ListItem>
                  ))}
                </List>
              </TableCell>
              <TableCell align="right">
                <DeleteButton handleDelete={(e) => handleDelete(e, group.id)}>
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

GroupList.propTypes = {
  groups: PropTypes.arrayOf(
    PropTypes.exact({
      id: PropTypes.number,
      name: PropTypes.string,
      members: PropTypes.arrayOf(
        PropTypes.exact({
          id: PropTypes.number,
          username: PropTypes.string,
        })
      ),
    })
  ),
};
