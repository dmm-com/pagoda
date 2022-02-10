import React, { FC } from "react";
import { BrowserRouter as Router, Switch, Route } from "react-router-dom";

import {
  aclPath,
  advancedSearchPath,
  advancedSearchResultPath,
  entitiesPath,
  entityEntriesPath,
  entityHistoryPath,
  entityPath,
  groupPath,
  groupsPath,
  importEntriesPath,
  importEntitiesPath,
  importGroupsPath,
  importUsersPath,
  jobsPath,
  newEntityPath,
  newEntryPath,
  newGroupPath,
  newUserPath,
  passwordPath,
  searchPath,
  showEntryPath,
  userPath,
  usersPath,
  loginPath,
  showEntryHistoryPath,
  entryPath,
} from "Routes";
import { Header } from "components/Header";
import { ACL } from "pages/ACL";
import { AdvancedSearch } from "pages/AdvancedSearch";
import { AdvancedSearchResults } from "pages/AdvancedSearchResults";
import { Dashboard } from "pages/Dashboard";
import { EditEntity } from "pages/EditEntity";
import { EditEntry } from "pages/EditEntry";
import { EditGroup } from "pages/EditGroup";
import { EditUser } from "pages/EditUser";
import { EditUserPassword } from "pages/EditUserPassword";
import { Entity } from "pages/Entity";
import { EntityHistory } from "pages/EntityHistory";
import { EntryList } from "pages/EntryList";
import { Group } from "pages/Group";
import { ImportEntity } from "pages/ImportEntity";
import { ImportEntry } from "pages/ImportEntry";
import { ImportGroup } from "pages/ImportGroup";
import { ImportUser } from "pages/ImportUser";
import { Job } from "pages/Job";
import { Login } from "pages/Login";
import { Search } from "pages/Search";
import { ShowEntry } from "pages/ShowEntry";
import { ShowEntryHistory } from "pages/ShowEntryHistory";
import { User } from "pages/User";

interface Props {
  customRoutes?: {
    path: string;
    routePath: string;
    component?: FC;
    render?: any;
  }[];
}

export const AppRouter: FC<Props> = ({ customRoutes }) => {
  return (
    <Router>
      <Switch>
        <Route path={loginPath()} component={Login} />
        <Route path="/">
          <Header />
          <Switch>
            {customRoutes &&
              customRoutes.map((r) => (
                <Route key={r.path} path={r.path}>
                  <Switch>
                    <Route
                      path={r.routePath}
                      component={r.component}
                      render={r.render}
                    />
                  </Switch>
                </Route>
              ))}

            <Route path={advancedSearchPath()} component={AdvancedSearch} />
            <Route
              path={advancedSearchResultPath()}
              component={AdvancedSearchResults}
            />
            <Route path={newEntryPath(":entityId")} component={EditEntry} />
            <Route path={showEntryPath(":entryId")} component={ShowEntry} />
            <Route
              path={importEntriesPath(":entityId")}
              component={ImportEntry}
            />
            <Route
              path={showEntryHistoryPath(":entryId")}
              component={ShowEntryHistory}
            />
            <Route path={entryPath(":entryId")} component={EditEntry} />
            <Route
              path={entityEntriesPath(":entityId")}
              component={EntryList}
            />
            <Route
              path={entityHistoryPath(":entityId")}
              component={EntityHistory}
            />
            <Route path={newEntityPath()} component={EditEntity} />
            <Route path={importEntitiesPath()} component={ImportEntity} />
            <Route path={entityPath(":entityId")} component={EditEntity} />
            <Route path={entitiesPath()} component={Entity} />
            <Route path={newGroupPath()} component={EditGroup} />
            <Route path={importGroupsPath()} component={ImportGroup} />
            <Route path={groupPath(":groupId")} component={EditGroup} />
            <Route path={groupsPath()} component={Group} />
            <Route path={jobsPath()} component={Job} />
            <Route path={aclPath(":objectId")} component={ACL} />
            <Route path={searchPath()} component={Search} />
            <Route path={newUserPath()} component={EditUser} />
            <Route path={importUsersPath()} component={ImportUser} />
            <Route
              path={passwordPath(":userId")}
              component={EditUserPassword}
            />
            <Route path={userPath(":userId")} component={EditUser} />
            <Route path={usersPath()} component={User} />
            <Route path="/" component={Dashboard} />
          </Switch>
        </Route>
      </Switch>
    </Router>
  );
};
