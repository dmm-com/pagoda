import React, {useEffect, useState} from "react";
import Button from "@material-ui/core/Button";
import {Table, TableBody, TableCell, TableContainer, TableHead, TablePagination, TableRow} from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import {Link} from "react-router-dom";
import EditIcon from '@material-ui/icons/Edit';
import HistoryIcon from '@material-ui/icons/History';
import GroupIcon from '@material-ui/icons/Group';
import DeleteIcon from '@material-ui/icons/Delete';
import {makeStyles} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import AironeBreadcrumbs from "../components/AironeBreadcrumbs";
import {getEntities} from "../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
    entityName: {
        margin: theme.spacing(1),
    },
}));

export default function Entity(props) {
    const classes = useStyles();
    const [entities, setEntities] = useState([]);
    const [page, setPage] = React.useState(0);
    const [rowsPerPage, setRowsPerPage] = React.useState(100);

    useEffect(() => {
        getEntities()
            .then(resp => resp.json())
            .then(data => setEntities(data.entities));
    }, []);

    const handleChangePage = (event, newPage) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event) => {
        setRowsPerPage(+event.target.value);
        setPage(0);
    };

    return (
        <div className="container-fluid">
            <AironeBreadcrumbs>
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography color="textPrimary">エンティティ一覧</Typography>
            </AironeBreadcrumbs>

            <div className="row">
                <div className="col">
                    <div className="float-left">
                        <Button className={classes.button} variant="outlined" color="primary">新規作成</Button>
                        <Button className={classes.button} variant="outlined" color="secondary">エクスポート</Button>
                        <Button className={classes.button} variant="outlined" color="secondary">インポート</Button>
                    </div>
                    <div className="float-right">
                    </div>
                </div>
            </div>

            <Paper>

                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>
                                    <span className={classes.entityName}>エンティティ名</span>
                                    <input className={classes.entityName} text='text' placeholder='絞り込む'/>
                                </TableCell>
                                <TableCell><Typography>備考</Typography></TableCell>
                                <TableCell align="right"/>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {entities.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((entity) => {
                                return (
                                    <TableRow>
                                        <TableCell>
                                            <Typography
                                                component={Link}
                                                to={`/new-ui/entities/${entity.id}`}>
                                                {entity.name}
                                            </Typography>
                                        </TableCell>
                                        <TableCell><Typography>{entity.note}</Typography></TableCell>
                                        <TableCell align="right">
                                            <Button
                                                variant="contained"
                                                color="primary"
                                                className={classes.button}
                                                startIcon={<EditIcon/>}
                                                component={Link}
                                                to={`/entity/edit/${entity.id}`}>
                                                エンティティ編集
                                            </Button>
                                            <Button
                                                variant="contained"
                                                color="primary"
                                                className={classes.button}
                                                startIcon={<HistoryIcon/>}
                                                component={Link}
                                                to={`/entity/history/${entity.id}`}>
                                                変更履歴
                                            </Button>
                                            <Button
                                                variant="contained"
                                                color="primary"
                                                className={classes.button}
                                                startIcon={<GroupIcon/>}
                                                component={Link}
                                                to={`/acl/${entity.id}`}>
                                                ACL
                                            </Button>
                                            <Button
                                                variant="contained"
                                                color="secondary"
                                                className={classes.button}
                                                startIcon={<DeleteIcon/>}
                                                component={Link}
                                                to={`/entity/do_delete/${entity.id}`}>
                                                削除
                                            </Button>
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
                    count={entities.length}
                    rowsPerPage={rowsPerPage}
                    page={page}
                    onChangePage={handleChangePage}
                    onChangeRowsPerPage={handleChangeRowsPerPage}
                />
            </Paper>
        </div>
    );
}
