import {
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
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { getACL } from "../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function ACL({}) {
  const classes = useStyles();
  const { objectId } = useParams();

  const [object, setObject] = useState([]);
  const [acltypes, setACLTypes] = useState([]);
  const [members, setMembers] = useState([]);

  useEffect(() => {
    getACL(objectId).then((data) => {
      setObject(data.object);
      setACLTypes(data.acltypes);
      setMembers(data.members);
    });
  }, []);

  const onSubmit = (event) => {
    event.preventDefault();
  };

  return (
    <div className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography color="textPrimary">ACL</Typography>
      </AironeBreadcrumbs>

      <Typography>{object.name} の ACL 設定</Typography>

      <form onSubmit={onSubmit}>
        <div className="container">
          <div className="row">
            <div className="col">
              <span className="float-left">
                公開：
                <input
                  type="checkbox"
                  value={object.is_public}
                  onChange={(e) =>
                    setObject({ ...object, is_public: e.target.checked })
                  }
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
              {members.map((member, index) => (
                <TableRow key={member.name}>
                  <TableCell>
                    <Typography>{member.name}</Typography>
                  </TableCell>
                  <TableCell align="left">
                    <select
                      name="acl"
                      value={member.current_permission}
                      onChange={(e) => {
                        if (members[index] !== undefined) {
                          members[index].current_permission = e.target.value;
                          setMembers([...members]);
                        }
                      }}
                    >
                      {acltypes.map((acltype) => (
                        <option key={acltype.id} value={acltype.id}>
                          {acltype.name}
                        </option>
                      ))}
                    </select>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </form>
    </div>
  );
}
