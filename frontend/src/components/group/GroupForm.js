import Typography from "@material-ui/core/Typography";
import { Select } from "@material-ui/core";
import Button from "@material-ui/core/Button";
import React, { useState } from "react";
import { makeStyles } from "@material-ui/core/styles";
import PropTypes from "prop-types";
import { createGroup, updateGroup } from "../../utils/AironeAPIClient";
import { useHistory } from "react-router-dom";

function multipleSelectedValues(event) {
  return Array.from(event.target.options, (o) => o)
    .filter((o) => o.selected)
    .map((o) => Number(o.value));
}

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export default function GroupForm({ users, group = {} }) {
  const classes = useStyles();
  const history = useHistory();

  const [name, setName] = useState(group.name ? group.name : "");
  const [members, setMembers] = useState(
    group.members ? group.members.map((m) => m.id) : []
  );

  const onSubmit = (event) => {
    if (group.id !== undefined) {
      updateGroup(group.id, name, members).then(() =>
        history.replace("/new-ui/groups")
      );
    } else {
      createGroup(name, members).then(() => history.replace("/new-ui/groups"));
    }

    event.preventDefault();
  };

  return (
    <form onSubmit={onSubmit}>
      <div>
        <Typography>グループ名</Typography>
        <input
          type="text"
          name="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required="required"
        />
      </div>
      <div>
        <Typography>ユーザ管理</Typography>
        <Select
          multiple
          native
          variant="outlined"
          onChange={(e) => setMembers(multipleSelectedValues(e))}
        >
          {users.map((user) => (
            <option selected={members.includes(user.id)} value={user.id}>
              {user.username}
            </option>
          ))}
        </Select>
      </div>
      <Button
        className={classes.button}
        type="submit"
        variant="contained"
        color="secondary"
      >
        保存
      </Button>
    </form>
  );
}

GroupForm.propTypes = {
  users: PropTypes.arrayOf(
    PropTypes.exact({
      id: PropTypes.number,
      username: PropTypes.string,
    })
  ),
  group: PropTypes.exact({
    id: PropTypes.number,
    name: PropTypes.string,
    members: PropTypes.arrayOf(
      PropTypes.exact({
        id: PropTypes.number,
        username: PropTypes.string,
      })
    ),
  }),
};
