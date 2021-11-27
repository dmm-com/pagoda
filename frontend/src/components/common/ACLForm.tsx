import {
  MenuItem,
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
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

import { updateACL } from "../../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  objectId: number;
  acl: any;
}

export const ACLForm: FC<Props> = ({ objectId, acl }) => {
  const classes = useStyles();
  const history = useHistory();

  const [isPublic, setIsPublic] = useState(acl.is_public);
  // TODO correct way to collect member permissions?
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

  const handleSubmit = async () => {
    // TODO better name?
    const aclSettings = acl.members.map((member) => {
      return {
        member_id: member.id,
        member_type: member.type,
        value: permissions[member.name],
      };
    });

    await updateACL(
      objectId,
      acl.name,
      acl.objtype,
      isPublic,
      acl.default_permission,
      aclSettings
    );

    history.go(0);
  };

  return (
    <form>
      <div className="container">
        <div className="row">
          <div className="col">
            <span className="float-left">
              公開：
              <input
                type="checkbox"
                name="is_public"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
              />
            </span>
            <span className="float-right">
              <Button
                className={classes.button}
                variant="contained"
                color="secondary"
                onClick={handleSubmit}
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
                      <MenuItem key={acltype.id} value={acltype.id}>
                        {acltype.name}
                      </MenuItem>
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
};
