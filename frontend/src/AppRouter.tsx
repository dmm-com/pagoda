import React, { FC } from "react";
import { BrowserRouter as Router, Switch, Route } from "react-router-dom";

import { CopyEntryPage } from "./pages/CopyEntryPage";
import { EditRolePage } from "./pages/EditRolePage";
import { EntryDetailsPage } from "./pages/EntryDetailsPage";
import { NotFoundErrorPage } from "./pages/NotFoundErrorPage";
import { RestoreEntryPage } from "./pages/RestoreEntryPage";
import { RolePage } from "./pages/RolePage";

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
  jobsPath,
  newEntityPath,
  newEntryPath,
  newGroupPath,
  newUserPath,
  userPath,
  usersPath,
  loginPath,
  showEntryHistoryPath,
  entryEditPath,
  entryDetailsPath,
  copyEntryPath,
  restoreEntryPath,
  rolesPath,
  rolePath,
  newRolePath,
  topPath,
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
import { EntityHistoryPage } from "pages/EntityHistoryPage";
import { EntityPage } from "pages/EntityPage";
import { EntryHistoryListPage } from "pages/EntryHistoryListPage";
import { EntryListPage } from "pages/EntryListPage";
import { GroupPage } from "pages/GroupPage";
import { JobPage } from "pages/JobPage";
import { LoginPage } from "pages/LoginPage";
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
            <Route
              path={copyEntryPath(":entityId", ":entryId")}
              component={CopyEntryPage}
            />
            <Route
              path={entryDetailsPath(":entityId", ":entryId")}
              component={EntryDetailsPage}
            />
            <Route
              path={restoreEntryPath(":entityId")}
              component={RestoreEntryPage}
            />
            <Route
              path={entryEditPath(":entityId", ":entryId")}
              component={EditEntryPage}
            />
            <Route
              path={showEntryHistoryPath(":entryId")}
              component={EntryHistoryListPage}
            />
            <Route
              path={entityEntriesPath(":entityId")}
              component={EntryListPage}
            />
            <Route
              path={entityHistoryPath(":entityId")}
              component={EntityHistoryPage}
            />
            <Route path={newEntityPath()} component={EditEntityPage} />
            <Route path={entityPath(":entityId")} component={EditEntityPage} />
            <Route path={entitiesPath()} component={EntityPage} />
            <Route path={newGroupPath()} component={EditGroupPage} />
            <Route path={groupPath(":groupId")} component={EditGroupPage} />
            <Route path={groupsPath()} component={GroupPage} />
            <Route path={jobsPath()} component={JobPage} />
            <Route path={aclPath(":objectId")} component={ACLPage} />
            <Route path={newUserPath()} component={EditUserPage} />
            <Route path={userPath(":userId")} component={EditUserPage} />
            <Route path={usersPath()} component={UserPage} />
            <Route path={newRolePath()} component={EditRolePage} />
            <Route path={rolePath(":roleId")} component={EditRolePage} />
            <Route path={rolesPath()} component={RolePage} />
            <Route exact path={topPath()} component={DashboardPage} />
            <Route component={NotFoundErrorPage} />
          </Switch>
        </Route>
      </Switch>
    </Router>
  );
};
