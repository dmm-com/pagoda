import React, {useEffect, useState} from "react";
import {makeStyles} from "@material-ui/core/styles";
import Button from "@material-ui/core/Button";
import {useParams} from "react-router-dom";
import {Table, TableBody, TableCell, TableHead, TableRow} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
}));

export default function EditUserPassword(props) {
    const classes = useStyles();
    const {userId} = useParams();

    const [name, setName] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [checkPassword, setCheckPassword] = useState("");

    const onSubmit = (event) => {
        event.preventDefault();
    };

    const onChangeName = (event) => {
        setName(event.target.value);
    };

    const onChangeNewPassword = (event) => {
        setNewPassword(event.target.value);
    };

    const onChangeCheckPassword = (event) => {
        setCheckPassword(event.target.value);
    };

    return (
        <form onSubmit={onSubmit}>
            <Typography>ユーザ編集</Typography>
            <Button className={classes.button} type="submit" variant="contained"
                    color="secondary">保存</Button>
            <Table className="table table-bordered">
                <TableBody>
                    <TableRow>
                        <TableHead>名前</TableHead>
                        <TableCell>
                            <input type="text" name="name" value={name} onChange={onChangeName} required="required"/>
                        </TableCell>
                    </TableRow>
                    <TableRow>
                        <TableHead>パスワード</TableHead>
                        <TableCell>
                            <dt><label htmlFor="new_password">New password</label></dt>
                            <input type="password" value={newPassword} onChange={onChangeNewPassword}/>
                            <dt><label htmlFor="chk_password">Confirm new password</label></dt>
                            <input type="password" value={checkPassword} onChange={onChangeCheckPassword}/>
                        </TableCell>
                    </TableRow>
                </TableBody>
            </Table>
        </form>
    );
}