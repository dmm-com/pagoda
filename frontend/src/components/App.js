import React from "react";
import ReactDOM from "react-dom";
import {
    BrowserRouter as Router,
    Switch,
    Route,
} from "react-router-dom";
import Grid from '@material-ui/core/Grid';
import LeftMenu from "./LeftMenu";
import Header from "./Header";
import Entity from "./Entity";
import Entry from "./Entry";

function App() {
    return (
        <Router>
            <Grid container>
                <Grid item xs={12}>
                    <Header/>
                </Grid>

                <Grid item xs={2}>
                    <LeftMenu/>
                </Grid>

                <Grid item xs={10}>
                    <Switch>
                        <Route path="/new-ui/advanced_search">
                            高度な検索
                        </Route>
                        <Route path="/new-ui/user">
                            ユーザ管理
                        </Route>
                        <Route path="/new-ui/group">
                            グループ管理
                        </Route>
                        <Route path="/new-ui/entities/:entityId">
                            <Entry />
                        </Route>
                        <Route path="/">
                            <Entity/>
                        </Route>
                    </Switch>
                </Grid>
            </Grid>
        </Router>
    );
}

ReactDOM.render(<App/>, document.getElementById("app"));
