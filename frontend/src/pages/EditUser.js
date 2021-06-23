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

export default function EditUser(props) {
    const classes = useStyles();
    const {userId} = useParams();

    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [isAdmin, setIsAdmin] = useState(false);

    const onSubmit = (event) => {
        event.preventDefault();
    };

    const onChangeName = (event) => {
        setName(event.target.value);
    };

    const onChangeEmail = (event) => {
        setEmail(event.target.value);
    };

    const onChangeIsAdmin = (event) => {
        setIsAdmin(event.target.value);
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
                        <TableHead>メールアドレス</TableHead>
                        <TableCell>
                            <input type="email" name="email" value={email} onChange={onChangeEmail}
                                   required="required"/>
                        </TableCell>
                    </TableRow>
                    <TableRow>
                        <TableHead>管理者権限を付与</TableHead>
                        <TableCell>
                            <input type="checkbox" name="is_superuser"
                                   value={isAdmin} onChange={onChangeIsAdmin}/>
                        </TableCell>
                    </TableRow>
                    {/*
                    {
                        (() => {
                            if (props.token) {
                                return <TableRow>
                                    <TableHead>AccessToken</TableHead>
                                    <TableCell>
                                        <p id='access_token'>{props.token}</p>
                                        <button type='button' id='refresh_token'
                                                className='btn btn-primary btn-sm'>Refresh
                                        </button>
                                    </TableCell>
                                </TableRow>;
                            }
                        })()
                    }
                    <TableRow>
                        <TableHead>AccessToken の有効期間 [sec]</TableHead>
                        <TableCell>
                            <p>
                                <input type="text" name="token_lifetime" value={props.token.lifetime}/>
                                (0 ~ 10^8 の範囲の整数を指定してください(0 を入力した場合は期限は無期限になります))
                            </p>
                            有効期限：{props.token.expire}
                        </TableCell>
                    </TableRow>
                    */}
                </TableBody>
            </Table>
        </form>
    );
}