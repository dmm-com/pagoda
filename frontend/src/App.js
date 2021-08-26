import React from "react";
import ReactDOM from "react-dom";
import { BrowserRouter as Router, Switch, Route } from "react-router-dom";
import Grid from "@material-ui/core/Grid";
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
import OperationHistory from "./pages/OperationHistory";
import ACL from "./pages/ACL";
import Import from "./pages/Import";
import EditUser from "./pages/EditUser";
import EditUserPassword from "./pages/EditUserPassword";
import EditGroup from "./pages/EditGroup";

const basePath = "/new-ui/";

function App() {
  return (
    <Router>
      <Grid container>
        <Grid item xs={12}>
          <Header />
        </Grid>

        <Grid item xs={2}>
          <LeftMenu />
        </Grid>

        <Grid item xs={10}>
          <Switch>
            <Route
              path={basePath + "advanced_search"}
              component={AdvancedSearch}
            />
            <Route
              path={basePath + "entities/:entityId/entries/new"}
              component={EditEntry}
            />
            <Route
              path={basePath + "entities/:entityId/entries/:entryId"}
              component={EditEntry}
            />
            <Route
              path={basePath + "entities/:entityId/entries"}
              component={Entry}
            />
            <Route
              path={basePath + "entities/:entityId/history"}
              component={OperationHistory}
            />
            <Route path={basePath + "entities/new"} component={EditEntity} />
            <Route
              path={basePath + "entities/:entityId"}
              component={EditEntity}
            />
            <Route path={basePath + "entities"} component={Entity} />
            <Route path={basePath + "groups/new"} component={EditGroup} />
            <Route path={basePath + "groups/:groupId"} component={EditGroup} />
            <Route path={basePath + "groups"} component={Group} />
            <Route path={basePath + "import"} component={Import} />
            <Route path={basePath + "jobs"} component={Job} />
            <Route path={basePath + "acl/:objectId"} component={ACL} />
            <Route path={basePath + "search"} component={SearchResults} />
            <Route path={basePath + "users/new"} component={EditUser} />
            <Route
              path={basePath + "users/:userId/password"}
              component={EditUserPassword}
            />
            <Route path={basePath + "users/:userId"} component={EditUser} />
            <Route path={basePath + "users"} component={User} />
            <Route path="/" component={Dashboard} />
          </Switch>
        </Grid>
      </Grid>
    </Router>
  );
}

ReactDOM.render(<App />, document.getElementById("app"));
