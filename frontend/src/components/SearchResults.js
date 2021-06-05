import {makeStyles} from "@material-ui/core/styles";
import {grey} from "@material-ui/core/colors";
import React, {useEffect, useState} from "react";
import {Breadcrumbs, Table, TableBody, TableCell, TableContainer, TableHead, TableRow} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import {Link} from "react-router-dom";
import Button from "@material-ui/core/Button";
import Paper from "@material-ui/core/Paper";
import EditIcon from "@material-ui/icons/Edit";
import DeleteIcon from "@material-ui/icons/Delete";
import SettingsIcon from '@material-ui/icons/Settings';

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
    entityName: {
        margin: theme.spacing(1),
    },
    breadcrumbs: {
        padding: theme.spacing(1),
        marginBottom: theme.spacing(1),
        backgroundColor: grey[300],
    },
}));

export default function SearchResults(props) {
    const classes = useStyles();
    const [results, setResults] = useState([]);

    useEffect(() => {
        // TODO implement internal API then call it here
        setResults([
            {
                name: 'test',
                attr1: 'val1',
                attr2: 'val2',
            },
        ])
    }, []);

    let fields = [];
    if (results.length > 0) {
        fields = Object.keys(results[0]);
    }

    return (
        <div className="container-fluid">
            <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography component={Link} to='/new-ui/advanced_search'>高度な検索</Typography>
                <Typography color="textPrimary">検索結果</Typography>
            </Breadcrumbs>

            <div className="row">
                <div className="col">
                    <div className="float-left">
                        <Typography>検索結果: ({results.length} 件)</Typography>
                        <Button className={classes.button} variant="outlined" startIcon={<SettingsIcon/>}
                                color="default">高度な検索</Button>
                        <Button className={classes.button} variant="outlined" color="primary">YAML 出力</Button>
                        <Button className={classes.button} variant="outlined" color="primary">CSV 出力</Button>
                    </div>
                    <div className="float-right">
                    </div>
                </div>
            </div>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            {fields.map((field) => {
                                return <TableCell><Typography>{field}</Typography></TableCell>;
                            })}
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {results.map((result) => {
                            return (
                                <TableRow>
                                    {fields.map((field) => {
                                        if (field in result) {
                                            return <TableCell><Typography>{result[field]}</Typography></TableCell>;
                                        }
                                    })}
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            </TableContainer>
        </div>
    );
}
