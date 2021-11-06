import {
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@material-ui/core";
import Button from "@material-ui/core/Button";
import Paper from "@material-ui/core/Paper";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import PropTypes from "prop-types";
import React, { useState } from "react";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export default function ACLForm({ acl }) {
  const classes = useStyles();

  const [isPublic, setIsPublic] = useState(acl.is_public);
  const [permissions, setPermissions] = useState(
    acl.members.reduce((obj, m) => {
      return {
        ...obj,
        [m.name]:
          m.current_permission > 0
            ? m.current_permission
            : acl.default_permission,
      };
    }, {})
  );
  console.log(permissions);

  const handleSubmit = (event) => {
    // TODO submit to API
    event.preventDefault();
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="container">
        <div className="row">
          <div className="col">
            <span className="float-left">
              公開：
              <input
                type="checkbox"
                name="is_public"
                value={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
              />
            </span>
            <span className="float-right">
              <Button
                className={classes.button}
                type="submit"
                variant="contained"
                color="secondary"
              >
                保存
              </Button>
            </span>
          </div>
        </div>
      </div>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>
                <Typography>ユーザ or グループ</Typography>
              </TableCell>
              <TableCell align="left">
                <Typography>権限</Typography>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {acl.members.map((member) => (
              <TableRow key={member.name}>
                <TableCell>
                  <Typography>{member.name}</Typography>
                </TableCell>
                <TableCell align="left">
                  <Select
                    value={permissions[member.name]}
                    onChange={(e) =>
                      setPermissions({
                        ...permissions,
                        [member.name]: e.target.value,
                      })
                    }
                  >
                    {acl.acltypes.map((acltype) => (
                      <option key={acltype.id} value={acltype.id}>
                        {acltype.name}
                      </option>
                    ))}
                  </Select>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </form>
  );
}

ACLForm.propTypes = {
  acl: PropTypes.shape({
    name: PropTypes.string.isRequired,
    is_public: PropTypes.bool.isRequired,
    default_permission: PropTypes.number.isRequired,
    acltypes: PropTypes.array.isRequired,
    members: PropTypes.arrayOf(
      PropTypes.shape({
        name: PropTypes.string.isRequired,
        current_permission: PropTypes.number.isRequired,
      })
    ).isRequired,
  }).isRequired,
};
