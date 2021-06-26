import {Table, TableBody, TableCell, TableContainer, TableHead, TableRow} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import {Link} from "react-router-dom";
import Button from "@material-ui/core/Button";
import Paper from "@material-ui/core/Paper";
import EditIcon from "@material-ui/icons/Edit";
import DeleteIcon from "@material-ui/icons/Delete";
import React, {useEffect, useState} from "react";
import {makeStyles} from "@material-ui/core/styles";
import AironeBreadcrumbs from "../components/AironeBreadcrumbs";
import {deleteEntry, getUsers} from "../utils/AironeAPIClient";
import ConfirmableButton from "../components/ConfirmableButton";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
    entityName: {
        margin: theme.spacing(1),
    },
}));

export default function User(props) {
    const classes = useStyles();
    const [users, setUsers] = useState([]);

    useEffect(() => {
        getUsers()
            .then(data => setUsers(data));
    }, []);

    const handleDelete = (event, userId) => {
        // TODO call delete API
    };

    return (
        <div className="container-fluid">
            <AironeBreadcrumbs>
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography color="textPrimary">ユーザ管理</Typography>
            </AironeBreadcrumbs>

            <div className="row">
                <div className="col">
                    <div className="float-left">
                        <Button
                            className={classes.button}
                            variant="outlined"
                            color="primary"
                            component={Link}
                            to={`/new-ui/users/new`}>
                            新規作成
                        </Button>
                        <Button className={classes.button} variant="outlined" color="secondary">エクスポート</Button>
                        <Button
                            className={classes.button}
                            variant="outlined"
                            color="secondary"
                            component={Link}
                            to={`/new-ui/import`}>
                            インポート
                        </Button>
                    </div>
                    <div className="float-right">
                    </div>
                </div>
            </div>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell><Typography>名前</Typography></TableCell>
                            <TableCell><Typography>メールアドレス</Typography></TableCell>
                            <TableCell><Typography>作成日時</Typography></TableCell>
                            <TableCell align="right"/>
                            <TableCell align="right"/>
                            <TableCell align="right"/>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {users.map((user) => {
                            return (
                                <TableRow>
                                    <TableCell><Typography>{user.name}</Typography></TableCell>
                                    <TableCell><Typography>{user.email}</Typography></TableCell>
                                    <TableCell><Typography>{user.created_at}</Typography></TableCell>
                                    <TableCell align="right">
                                        <Button
                                            variant="contained"
                                            color="primary"
                                            className={classes.button}
                                            startIcon={<EditIcon/>}
                                            component={Link}
                                            to={`/new-ui/users/${user.id}`}>
                                            編集
                                        </Button>
                                    </TableCell>
                                    <TableCell align="right">
                                        <Button
                                            variant="contained"
                                            color="primary"
                                            className={classes.button}
                                            startIcon={<EditIcon/>}
                                            component={Link}
                                            to={`/new-ui/users/${user.id}/password`}>
                                            パスワード変更
                                        </Button>
                                    </TableCell>
                                    <TableCell align="right">
                                        <ConfirmableButton
                                            variant="contained"
                                            color="secondary"
                                            className={classes.button}
                                            startIcon={<DeleteIcon/>}
                                            component={Link}
                                            dialogTitle="本当に削除しますか？"
                                            onClickYes={(e) => handleDelete(e, user.id)}>
                                            削除
                                        </ConfirmableButton>
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            </TableContainer>
        </div>
    );
}
