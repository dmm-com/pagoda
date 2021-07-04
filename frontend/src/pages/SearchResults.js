import {makeStyles} from "@material-ui/core/styles";
import React, {useEffect, useState} from "react";
import {Table, TableBody, TableCell, TableContainer, TableHead, TableRow} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import {Link} from "react-router-dom";
import Button from "@material-ui/core/Button";
import Paper from "@material-ui/core/Paper";
import SettingsIcon from '@material-ui/icons/Settings';
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import {getAdvancedSearchResults} from "../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
    entityName: {
        margin: theme.spacing(1),
    },
}));

export default function SearchResults({}) {
    const classes = useStyles();
    const [results, setResults] = useState([]);

    useEffect(() => {
        getAdvancedSearchResults()
            .then(data => setResults(data));
    }, []);

    let fields = [];
    if (results.length > 0) {
        fields = Object.keys(results[0]);
    }

    return (
        <div className="container-fluid">
            <AironeBreadcrumbs>
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography component={Link} to='/new-ui/advanced_search'>高度な検索</Typography>
                <Typography color="textPrimary">検索結果</Typography>
            </AironeBreadcrumbs>

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
                            {fields.map((field) =>
                                <TableCell><Typography>{field}</Typography></TableCell>
                            )}
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {results.map((result) =>
                            <TableRow>
                                {fields.map((field) => {
                                    if (field in result) {
                                        return <TableCell><Typography>{result[field]}</Typography></TableCell>;
                                    }
                                })}
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>
        </div>
    );
}
