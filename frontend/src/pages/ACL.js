import React, {useEffect, useState} from "react";
import {getACL} from "../utils/AironeAPIClient";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import Typography from "@material-ui/core/Typography";
import {Link, useParams} from "react-router-dom";
import Button from "@material-ui/core/Button";
import {Table, TableBody, TableCell, TableContainer, TableHead, TableRow} from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import {makeStyles} from "@material-ui/core/styles";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
}));

export default function ACL({}) {
    const classes = useStyles();
    const {objectId} = useParams();

    const [object, setObject] = useState([]);
    const [acltypes, setACLTypes] = useState([]);
    const [members, setMembers] = useState([]);

    useEffect(() => {
        getACL(objectId)
            .then(data => {
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
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography color="textPrimary">ACL</Typography>
            </AironeBreadcrumbs>

            <Typography>{object.name} の ACL 設定</Typography>

            <form onSubmit={onSubmit}>
                <div className="container">
                    <div className="row">
                        <div className="col">
                            <span className="float-left">
                                公開：<input type="checkbox" name="is_public" checked={object.is_public}/>
                            </span>
                            <span className="float-right">
                                <Button className={classes.button} type="submit" variant="contained"
                                        color="secondary">保存</Button>
                            </span>
                        </div>
                    </div>
                </div>

                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell><Typography>ユーザ or グループ</Typography></TableCell>
                                <TableCell align="left"><Typography>権限</Typography></TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {members.map((member) =>
                                <TableRow>
                                    <TableCell><Typography>{member.name}</Typography></TableCell>
                                    <TableCell align="left">
                                        <select name="acl">
                                            {acltypes.map((acltype) => {
                                                if (acltype.id === member.current_permission) {
                                                    return <option value={acltype.id}
                                                                   selected="selected">{acltype.name}</option>;
                                                } else {
                                                    return <option value={acltype.id}>{acltype.name}</option>;
                                                }
                                            })}
                                        </select>
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            </form>

        </div>
    );
}
