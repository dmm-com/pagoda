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
import { ACLPage } from "pages/ACLPage";
import { AdvancedSearchPage } from "pages/AdvancedSearchPage";
import { AdvancedSearchResultsPage } from "pages/AdvancedSearchResultsPage";
import { DashboardPage } from "pages/DashboardPage";
import { EditEntityPage } from "pages/EditEntityPage";
import { EditEntryPage } from "pages/EditEntryPage";
import { EditGroupPage } from "pages/EditGroupPage";
import { EditUserPage } from "pages/EditUserPage";
import { EditUserPasswordPage } from "pages/EditUserPasswordPage";
import { EntityHistoryPage } from "pages/EntityHistoryPage";
import { EntityPage } from "pages/EntityPage";
import { EntryListPage } from "pages/EntryListPage";
import { GroupPage } from "pages/GroupPage";
import { ImportEntityPage } from "pages/ImportEntityPage";
import { ImportEntryPage } from "pages/ImportEntryPage";
import { ImportGroupPage } from "pages/ImportGroupPage";
import { ImportUserPage } from "pages/ImportUserPage";
import { JobPage } from "pages/JobPage";
import { LoginPage } from "pages/LoginPage";
import { SearchPage } from "pages/SearchPage";
import { ShowEntryHistoryPage } from "pages/ShowEntryHistoryPage";
import { ShowEntryPage } from "pages/ShowEntryPage";
import { UserPage } from "pages/UserPage";

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
        <Route path={loginPath()} component={LoginPage} />
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

            <Route path={advancedSearchPath()} component={AdvancedSearchPage} />
            <Route
              path={advancedSearchResultPath()}
              component={AdvancedSearchResultsPage}
            />
            <Route path={newEntryPath(":entityId")} component={EditEntryPage} />
            <Route path={showEntryPath(":entryId")} component={ShowEntryPage} />
            <Route
              path={importEntriesPath(":entityId")}
              component={ImportEntryPage}
            />
            <Route
              path={showEntryHistoryPath(":entryId")}
              component={ShowEntryHistoryPage}
            />
            <Route path={entryPath(":entryId")} component={EditEntryPage} />
            <Route
              path={entityEntriesPath(":entityId")}
              component={EntryListPage}
            />
            <Route
              path={entityHistoryPath(":entityId")}
              component={EntityHistoryPage}
            />
            <Route path={newEntityPath()} component={EditEntityPage} />
            <Route path={importEntitiesPath()} component={ImportEntityPage} />
            <Route path={entityPath(":entityId")} component={EditEntityPage} />
            <Route path={entitiesPath()} component={EntityPage} />
            <Route path={newGroupPath()} component={EditGroupPage} />
            <Route path={importGroupsPath()} component={ImportGroupPage} />
            <Route path={groupPath(":groupId")} component={EditGroupPage} />
            <Route path={groupsPath()} component={GroupPage} />
            <Route path={jobsPath()} component={JobPage} />
            <Route path={aclPath(":objectId")} component={ACLPage} />
            <Route path={searchPath()} component={SearchPage} />
            <Route path={newUserPath()} component={EditUserPage} />
            <Route path={importUsersPath()} component={ImportUserPage} />
            <Route
              path={passwordPath(":userId")}
              component={EditUserPasswordPage}
            />
            <Route path={userPath(":userId")} component={EditUserPage} />
            <Route path={usersPath()} component={UserPage} />
            <Route path="/" component={DashboardPage} />
          </Switch>
        </Route>
      </Switch>
    </Router>
  );
};
