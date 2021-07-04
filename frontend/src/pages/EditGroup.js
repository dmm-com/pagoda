import React, {useEffect, useState} from "react";
import {makeStyles} from "@material-ui/core/styles";
import Button from "@material-ui/core/Button";
import {Link, useParams} from "react-router-dom";
import {Select, Table, TableBody, TableCell, TableHead, TableRow} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import {getGroups, getUsers} from "../utils/AironeAPIClient";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
}));

export default function EditGroup(props) {
    const classes = useStyles();

    const [name, setName] = useState("");
    const [users, setUsers] = useState([]);

    useEffect(() => {
        getUsers()
            .then(data => setUsers(data));
    }, []);

    const onSubmit = (event) => {
        event.preventDefault();
    };

    const onChangeName = (event) => {
        setName(event.target.value);
    };

    return (
        <div>
            <AironeBreadcrumbs>
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography component={Link} to='/new-ui/groups'>グループ管理</Typography>
                <Typography color="textPrimary">グループ編集</Typography>
            </AironeBreadcrumbs>

            <form onSubmit={onSubmit}>
                <div>
                    <Typography>グループ名</Typography>
                    <input type="text" name="name" value={name} onChange={onChangeName} required="required"/>
                </div>
                <div>
                    <Typography>ユーザ管理</Typography>
                    <Select
                        multiple
                        native
                        variant="outlined">
                        {users.map((user) => (
                            <option value={user.id}>
                                {user.name}
                            </option>
                        ))}
                    </Select>
                </div>
                <Button className={classes.button} type="submit" variant="contained"
                        color="secondary">保存</Button>
            </form>
        </div>
    );
}