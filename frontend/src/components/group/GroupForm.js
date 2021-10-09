import { Select } from "@material-ui/core";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import PropTypes from "prop-types";
import React, { useState } from "react";
import { useHistory } from "react-router-dom";

import { groupsPath } from "../../Routes";
import { createGroup, updateGroup } from "../../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function GroupForm({ users, group }) {
  const classes = useStyles();
  const history = useHistory();

  const [name, setName] = useState(group?.name ?? "");
  const [members, setMembers] = useState(group?.members.map((m) => m.id) ?? []);

  const handleChangeSelectedOptions = (event) => {
    const options = Array.from(event.target.options, (o) => o);
    const values = options.filter((o) => o.selected).map((o) => o.value);
    setMembers(values);
  };

  const handleSubmit = (event) => {
    if (group.id !== undefined) {
      updateGroup(group.id, name, members).then(() =>
        history.replace(groupsPath())
      );
    } else {
      createGroup(name, members).then(() => history.replace(groupsPath()));
    }

    event.preventDefault();
  };

  return (
    <form onSubmit={handleSubmit}>
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
          value={members}
          onChange={handleChangeSelectedOptions}
        >
          {users.map((user) => (
            <option key={user.id} value={user.id}>
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
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      username: PropTypes.string.isRequired,
    })
  ).isRequired,
  group: PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    members: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.number,
        username: PropTypes.string,
      })
    ).isRequired,
  }),
};
