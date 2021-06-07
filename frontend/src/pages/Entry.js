import React, {useEffect, useState} from "react";
import Button from "@material-ui/core/Button";
import {useParams, Link} from "react-router-dom";
import {makeStyles} from "@material-ui/core/styles";
import {
    Divider,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TablePagination,
    TableRow
} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import Paper from "@material-ui/core/Paper";
import DeleteIcon from "@material-ui/icons/Delete";
import Tab from "@material-ui/core/Tab";
import Tabs from "@material-ui/core/Tabs";
import AironeBreadcrumbs from "../components/AironeBreadcrumbs";
import {deleteEntry, getEntries} from "../utils/AironeAPIClient";
import ConfirmableButton from "../components/ConfirmableButton";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
}));

export default function Entry(props) {
    const classes = useStyles();
    let {entityId} = useParams();
    const [entries, setEntries] = useState([]);
    const [tabValue, setTabValue] = useState(1);
    const [updated, setUpdated] = useState(false);

    const [page, setPage] = React.useState(0);
    const [rowsPerPage, setRowsPerPage] = React.useState(100);

    useEffect(() => {
        getEntries(entityId)
            .then(resp => resp.json())
            .then(data => setEntries(data.results))
            .then(_ => setUpdated(false));
    }, [updated]);

    const handleTabChange = (event, newValue) => {
        setTabValue(newValue);
    };

    const handleDelete = (event, entryId) => {
        deleteEntry(entryId)
            .then(_ => setUpdated(true));
    };

    const handleChangePage = (event, newPage) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event) => {
        setRowsPerPage(+event.target.value);
        setPage(0);
    };

    return (
        <div>
            <AironeBreadcrumbs>
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography component={Link} to='/new-ui/entities'>エンティティ一覧</Typography>
                <Typography color="textPrimary">エントリ一覧</Typography>
            </AironeBreadcrumbs>

            <div className="row">
                <div className="col">
                    <div className="float-left">
                        <Button
                            variant="contained"
                            color="primary"
                            className={classes.button}
                            component={Link}
                            to={`/new-ui/entities/${entityId}/entries/new`}>
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

            <Divider />

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
                <Paper>
                    <TableContainer component={Paper}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell><Typography>エントリ名</Typography></TableCell>
                                    <TableCell align="right"/>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {entries.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((entry) => {
                                    return (
                                        <TableRow>
                                            <TableCell>
                                                <Typography>{entry.name}</Typography>
                                            </TableCell>
                                            <TableCell align="right">
                                                <ConfirmableButton
                                                    variant="contained"
                                                    color="secondary"
                                                    className={classes.button}
                                                    startIcon={<DeleteIcon/>}
                                                    component={Link}
                                                    dialogTitle="本当に削除しますか？"
                                                    onClickYes={(e) => handleDelete(e, entry.id)}>
                                                    削除
                                                </ConfirmableButton>
                                            </TableCell>
                                        </TableRow>
                                    );
                                })}
                            </TableBody>
                        </Table>
                    </TableContainer>
                    <TablePagination
                        rowsPerPageOptions={[100, 250, 1000]}
                        component="div"
                        count={entries.length}
                        rowsPerPage={rowsPerPage}
                        page={page}
                        onChangePage={handleChangePage}
                        onChangeRowsPerPage={handleChangeRowsPerPage}
                    />
                </Paper>
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
