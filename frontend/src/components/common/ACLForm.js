import { makeStyles } from "@material-ui/core/styles";
import Button from "@material-ui/core/Button";
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
import React from "react";
import PropTypes from "prop-types";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export default function ACLForm({ acl }) {
  const classes = useStyles();

  const onSubmit = (event) => {
    // TODO submit to API
    event.preventDefault();
  };

  return (
    <form onSubmit={onSubmit}>
      <div className="container">
        <div className="row">
          <div className="col">
            <span className="float-left">
              公開：
              <input
                type="checkbox"
                name="is_public"
                checked={acl.object.is_public}
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
              <TableRow>
                <TableCell>
                  <Typography>{member.name}</Typography>
                </TableCell>
                <TableCell align="left">
                  <select name="acl">
                    {acl.acltypes.map((acltype) => {
                      if (acltype.id === member.current_permission) {
                        return (
                          <option value={acltype.id} selected="selected">
                            {acltype.name}
                          </option>
                        );
                      } else {
                        return (
                          <option value={acltype.id}>{acltype.name}</option>
                        );
                      }
                    })}
                  </select>
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
  acl: PropTypes.object.isRequired,
};
