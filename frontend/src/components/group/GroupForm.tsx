import { Select } from "@material-ui/core";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import React, { ChangeEvent, FC, useState } from "react";
import { useHistory } from "react-router-dom";

import { groupsPath } from "../../Routes";
import { createGroup, updateGroup } from "../../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  users: {
    id: number;
    username: string;
  }[];
  group?: {
    id: number;
    name: string;
    members: {
      id: number;
      username: string;
    }[];
  };
}

export const GroupForm: FC<Props> = ({ users, group }) => {
  const classes = useStyles();
  const history = useHistory();

  const [name, setName] = useState(group?.name ?? "");
  const [members, setMembers] = useState<number[]>(
    group?.members.map((m) => m.id) ?? []
  );

  const handleChangeSelectedOptions = (
    event: ChangeEvent<HTMLSelectElement>
  ) => {
    const options = Array.from(event.target.options, (o) => o);
    const values = options
      .filter((o) => o.selected)
      .map((o) => Number(o.value));
    setMembers(values);
  };

  const handleSubmit = async (event) => {
    if (group.id !== undefined) {
      await updateGroup(group.id, name, members);
      history.replace(groupsPath());
    } else {
      await createGroup(name, members);
      history.replace(groupsPath());
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
          required={true}
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
};
