import React from "react";
import ReactDOM from "react-dom";
import {
    BrowserRouter as Router,
    Switch,
    Route,
} from "react-router-dom";
import Grid from '@material-ui/core/Grid';
import LeftMenu from "./components/LeftMenu";
import Header from "./components/Header";
import Entity from "./pages/Entity";
import Entry from "./pages/Entry";
import Dashboard from "./pages/Dashboard";
import User from "./pages/User";
import Group from "./pages/Group";
import Job from "./pages/Job";
import SearchResults from "./pages/SearchResults";
import AdvancedSearch from "./pages/AdvancedSearch";

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
                            <AdvancedSearch/>
                        </Route>
                        <Route path="/new-ui/user">
                            <User/>
                        </Route>
                        <Route path="/new-ui/group">
                            <Group/>
                        </Route>
                        <Route path="/new-ui/entities/:entityId">
                            <Entry/>
                        </Route>
                        <Route path="/new-ui/entities">
                            <Entity/>
                        </Route>
                        <Route path="/new-ui/jobs">
                            <Job/>
                        </Route>
                        <Route path="/new-ui/search">
                            <SearchResults/>
                        </Route>
                        <Route path="/">
                            <Dashboard/>
                        </Route>
                    </Switch>
                </Grid>
            </Grid>
        </Router>
    );
}

ReactDOM.render(<App/>, document.getElementById("app"));
