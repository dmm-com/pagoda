import { Select } from "@material-ui/core";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import { withStyles } from "@material-ui/core/styles";
import PropTypes from "prop-types";
import React from "react";
import { withRouter } from "react-router-dom";

import { groupsPath } from "../../Routes";
import { createGroup, updateGroup } from "../../utils/AironeAPIClient";

export class GroupForm extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      name: props.group?.name ?? "",
      members: props.group?.members
        ? props.group?.members.map((m) => m.id)
        : [],
    };
  }

  handleChangeSelectedOptions(event) {
    const options = Array.from(event.target.options, (o) => o);
    const values = options.filter((o) => o.selected).map((o) => o.value);

    this.setState({ members: values });
  }

  handleSubmit(event) {
    const { group, history } = this.props;
    const { name, members } = this.state;

    if (group && group.id !== undefined) {
      updateGroup(group.id, name, members).then(() => {
        history.replace(groupsPath());
      });
    } else {
      createGroup(name, members).then(() => {
        history.replace(groupsPath());
      });
    }

    event.preventDefault();
  }

  render() {
    const { users, history, classes } = this.props;
    const { name, members } = this.state;

    return (
      <form onSubmit={this.handleSubmit.bind(this)}>
        <div>
          <Typography>グループ名 (tmp02)</Typography>
          <input
            type="text"
            name="name"
            value={name}
            onChange={(e) => this.setState({ name: e.target.value })}
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
            onChange={this.handleChangeSelectedOptions.bind(this)}
          >
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.username}
              </option>
            ))}
          </Select>
        </div>
        <Button
          //className={classes.button}
          type="submit"
          variant="contained"
          color="secondary"
        >
          保存
        </Button>
      </form>
    );
  }
}

const styles = (theme) => ({
  button: {
    margin: theme.spacing(1),
  },
});

//export class GroupForm = withRouter(withStyles(styles)(_GroupForm));
withRouter(withStyles(styles)(GroupForm));

GroupForm.propTypes = {
  users: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      username: PropTypes.string.isRequired,
    })
  ).isRequired,
  group: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    members: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.number.isRequired,
        username: PropTypes.string.isRequired,
      })
    ),
  }),
};
