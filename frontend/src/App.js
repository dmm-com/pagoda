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
import EditEntity from "./pages/EditEntity";
import EditEntry from "./pages/EditEntry";

const basePath = '/new-ui/';

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
                        <Route path={basePath + "advanced_search"} component={AdvancedSearch}/>
                        <Route path={basePath + "user"} component={User}/>
                        <Route path={basePath + "group"} component={Group}/>
                        <Route path={basePath + "entities/:entityId/entries/new"} component={EditEntry}/>
                        <Route path={basePath + "entities/:entityId/entries/:entryId"} component={EditEntry}/>
                        <Route path={basePath + "entities/new"} component={EditEntity}/>
                        <Route path={basePath + "entities/:entityId"} component={Entry}/>
                        <Route path={basePath + "entities"} component={Entity}/>
                        <Route path={basePath + "jobs"} component={Job}/>
                        <Route path={basePath + "search"} component={SearchResults}/>
                        <Route path="/" component={Dashboard}/>
                    </Switch>
                </Grid>
            </Grid>
        </Router>
    );
}

ReactDOM.render(<App/>, document.getElementById("app"));
