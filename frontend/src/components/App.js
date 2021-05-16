import React from "react";
import ReactDOM from "react-dom";
import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';

import LeftMenu from "./LeftMenu";
import Header from "./Header";
import Dashboard from "./Dashboard";

function App() {
    return (
        <Grid container>
            <Grid item xs={12}>
                <Paper>
                    <Header/>
                </Paper>
            </Grid>
            <Grid item xs={2}>
                <Paper>
                    <LeftMenu/>
                </Paper>
            </Grid>
            <Grid item xs={10}>
                <Paper>
                    <Dashboard/>
                </Paper>
            </Grid>
        </Grid>
    );
}

ReactDOM.render(<App/>, document.getElementById("app"));
