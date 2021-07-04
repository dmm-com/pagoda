import {makeStyles} from "@material-ui/core/styles";
import React, {useEffect, useState} from "react";
import {
    List,
    ListItem,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow
} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import {Link} from "react-router-dom";
import Button from "@material-ui/core/Button";
import Paper from "@material-ui/core/Paper";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import {getJobs} from "../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
    entityName: {
        margin: theme.spacing(1),
    },
}));

export default function Job(props) {
    const classes = useStyles();
    const [jobs, setJobs] = useState([]);

    useEffect(() => {
        getJobs()
            .then(data => setJobs(data));
    }, []);

    return (
        <div className="container-fluid">
            <AironeBreadcrumbs>
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography color="textPrimary">ジョブ一覧</Typography>
            </AironeBreadcrumbs>

            <div className="row">
                <div className="col">
                    <div className="float-left">
                        <Button className={classes.button} variant="outlined" color="primary">全件表示</Button>
                    </div>
                    <div className="float-right">
                    </div>
                </div>
            </div>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell><Typography>対象エントリ</Typography></TableCell>
                            <TableCell><Typography>操作</Typography></TableCell>
                            <TableCell><Typography>状況</Typography></TableCell>
                            <TableCell><Typography>実行時間</Typography></TableCell>
                            <TableCell><Typography>実行日時</Typography></TableCell>
                            <TableCell align="right"><Typography>備考</Typography></TableCell>
                            <TableCell align="right"/>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {jobs.map((job) => {
                            return (
                                <TableRow>
                                    <TableCell><Typography>{job.entry}</Typography></TableCell>
                                    <TableCell><Typography>{job.operation}</Typography></TableCell>
                                    <TableCell><Typography>{job.status}</Typography></TableCell>
                                    <TableCell><Typography>{job.duration}</Typography></TableCell>
                                    <TableCell><Typography>{job.created_at}</Typography></TableCell>
                                    <TableCell align="right"><Typography>{job.note}</Typography></TableCell>
                                    <TableCell align="right">
                                        <List>
                                            <ListItem>
                                                <Button
                                                    variant="contained"
                                                    color="primary"
                                                    className={classes.button}
                                                    component={Link}
                                                    to={`/jobs/${job.id}/rerun`}>
                                                    Re-run
                                                </Button>
                                            </ListItem>
                                            <ListItem>
                                                <Button
                                                    variant="contained"
                                                    color="secondary"
                                                    className={classes.button}
                                                    component={Link}
                                                    to={`/jobs/${job.id}/cancel`}>
                                                    Cancel
                                                </Button>
                                            </ListItem>
                                        </List>
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
