import {
  Box,
  Button,
  Checkbox,
  MenuItem,
  Paper,
  Select,
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
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

import { updateACL } from "../../utils/AironeAPIClient";

const useStyles = makeStyles<Theme>((theme) => ({
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
      <Box className="container">
        <Box className="row">
          <Box className="col">
            <span className="float-left">
              公開：
              <Checkbox
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
          </Box>
        </Box>
      </Box>

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
