import React, {useEffect, useState} from "react";
import Button from "@material-ui/core/Button";
import {useParams, Link} from "react-router-dom";
import {makeStyles} from "@material-ui/core/styles";
import {Breadcrumbs, Table, TableBody, TableCell, TableContainer, TableHead, TableRow} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import Paper from "@material-ui/core/Paper";
import DeleteIcon from "@material-ui/icons/Delete";
import {grey} from "@material-ui/core/colors";
import Tab from "@material-ui/core/Tab";
import Tabs from "@material-ui/core/Tabs";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
    breadcrumbs: {
        padding: theme.spacing(1),
        marginBottom: theme.spacing(1),
        backgroundColor: grey[300],
    },
}));

export default function Entry(props) {
    const classes = useStyles();
    let {entityId} = useParams();
    const [entries, setEntries] = useState([]);
    const [tabValue, setTabValue] = useState(0);

    useEffect(() => {
        fetch(`/entry/api/v1/get_entries/${entityId}`)
            .then(resp => resp.json())
            .then(data => setEntries(data.results));
    }, []);

    const handleTabChange = (event, newValue) => {
        setTabValue(newValue);
    };

    return (
        <div>
            <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography component={Link} to='/new-ui/entities'>エンティティ一覧</Typography>
                <Typography color="textPrimary">エントリ一覧</Typography>
            </Breadcrumbs>

            <div className="row">
                <div className="col">
                    <div className="float-left">
                        <Button
                            variant="contained"
                            color="primary"
                            className={classes.button}
                            component={Link}
                            to={`/entry/create/${entityId}`}>
                            エントリ作成
                        </Button>
                        <Button
                            variant="contained"
                            className={classes.button}
                            component={Link}
                            to={`/entity/edit/${entityId}`}>
                            エンティティ編集
                        </Button>
                        <Button
                            variant="contained"
                            className={classes.button}
                            component={Link}
                            to={`/acl/${entityId}`}>
                            エンティティの ACL
                        </Button>
                        <Button
                            variant="contained"
                            color="secondary"
                            className={classes.button}>
                            エクスポート
                        </Button>
                        <Button
                            variant="contained"
                            color="secondary"
                            className={classes.button}
                            component={Link}
                            to={`/entry/import/${entityId}`}>
                            インポート
                        </Button>
                        <Button
                            variant="contained"
                            className={classes.button}>
                            CSV で出力
                        </Button>
                    </div>
                </div>
            </div>

            <Tabs value={tabValue} onChange={handleTabChange}>
                <Tab label="ダッシュボード" index={0}/>
                <Tab label="エントリ一覧" index={1}/>
                <Tab label="ダッシュボードの設定" index={2}/>
                <Tab label="削除エントリの復旧" index={3}/>
            </Tabs>

            <div hidden={tabValue !== 0}>
                ダッシュボード
            </div>

            <div hidden={tabValue !== 1}>
                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell><Typography>エントリ名</Typography></TableCell>
                                <TableCell align="right"/>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {entries.map((entry) => {
                                return (
                                    <TableRow>
                                        <TableCell>
                                            <Typography>{entry.name}</Typography>
                                        </TableCell>
                                        <TableCell align="right">
                                            <Button
                                                variant="contained"
                                                color="secondary"
                                                className={classes.button}
                                                startIcon={<DeleteIcon/>}
                                                component={Link}
                                                to={`/entry/do_delete/${entry.id}`}>
                                                削除
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                </TableContainer>
            </div>

            <div hidden={tabValue !== 2}>
                ダッシュボードの設定
            </div>

            <div hidden={tabValue !== 3}>
                削除エントリの復旧
            </div>
        </div>
    );
}
