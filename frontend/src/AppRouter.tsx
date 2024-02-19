import React, { FC } from "react";
import { RouteComponentProps } from "react-router";
import { Route, BrowserRouter as Router, Switch } from "react-router-dom";

import { ErrorHandler } from "./ErrorHandler";
import { ACLHistoryPage } from "./pages/ACLHistoryPage";
import { EntryCopyPage } from "./pages/EntryCopyPage";
import { EntryDetailsPage } from "./pages/EntryDetailsPage";
import { EntryRestorePage } from "./pages/EntryRestorePage";
import { NotFoundErrorPage } from "./pages/NotFoundErrorPage";
import { RoleEditPage } from "./pages/RoleEditPage";
import { RoleListPage } from "./pages/RoleListPage";

import {
  aclHistoryPath,
  aclPath,
  advancedSearchPath,
  advancedSearchResultPath,
  copyEntryPath,
  editEntityPath,
  editTriggerPath,
  entitiesPath,
  entityEntriesPath,
  entityHistoryPath,
  entryDetailsPath,
  entryEditPath,
  groupPath,
  groupsPath,
  jobsPath,
  loginPath,
  newEntityPath,
  newEntryPath,
  newGroupPath,
  newRolePath,
  newTriggerPath,
  newUserPath,
  restoreEntryPath,
  rolePath,
  rolesPath,
  showEntryHistoryPath,
  topPath,
  triggersPath,
  userPath,
  usersPath,
} from "Routes";
import { Header } from "components/Header";
import { ACLEditPage } from "pages/ACLEditPage";
import { AdvancedSearchPage } from "pages/AdvancedSearchPage";
import { AdvancedSearchResultsPage } from "pages/AdvancedSearchResultsPage";
import { DashboardPage } from "pages/DashboardPage";
import { EntityEditPage } from "pages/EntityEditPage";
import { EntityHistoryPage } from "pages/EntityHistoryPage";
import { EntityListPage } from "pages/EntityListPage";
import { EntryEditPage } from "pages/EntryEditPage";
import { EntryHistoryListPage } from "pages/EntryHistoryListPage";
import { EntryListPage } from "pages/EntryListPage";
import { GroupEditPage } from "pages/GroupEditPage";
import { GroupListPage } from "pages/GroupListPage";
import { JobListPage } from "pages/JobListPage";
import { LoginPage } from "pages/LoginPage";
import { TriggerEditPage } from "pages/TriggerEditPage";
import { TriggerListPage } from "pages/TriggerListPage";
import { UserEditPage } from "pages/UserEditPage";
import { UserListPage } from "pages/UserListPage";

interface Props {
  customRoutes?: {
    path: string;
    routePath: string;
    component?: FC;
    render?: (
      props: RouteComponentProps<{ [K: string]: string | undefined }>
    ) => React.ReactNode;
  }[];
}

export const AppRouter: FC<Props> = ({ customRoutes }) => {
  return (
    <Router>
      <ErrorHandler>
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

              <Route
                path={advancedSearchPath()}
                component={AdvancedSearchPage}
              />
              <Route
                path={advancedSearchResultPath()}
                component={AdvancedSearchResultsPage}
              />
              <Route
                path={newEntryPath(":entityId")}
                component={EntryEditPage}
              />
              <Route
                path={copyEntryPath(":entityId", ":entryId")}
                component={EntryCopyPage}
              />
              <Route
                path={entryDetailsPath(":entityId", ":entryId")}
                component={EntryDetailsPage}
              />
              <Route
                path={restoreEntryPath(":entityId")}
                component={EntryRestorePage}
              />
              <Route
                path={entryEditPath(":entityId", ":entryId")}
                component={EntryEditPage}
              />
              <Route
                path={showEntryHistoryPath(":entityId", ":entryId")}
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
              <Route path={newEntityPath()} component={EntityEditPage} />
              <Route
                path={editEntityPath(":entityId")}
                component={EntityEditPage}
              />
              <Route path={entitiesPath()} component={EntityListPage} />
              <Route path={newTriggerPath()} component={TriggerEditPage} />
              <Route
                path={editTriggerPath(":triggerId")}
                component={TriggerEditPage}
              />
              <Route path={triggersPath()} component={TriggerListPage} />
              <Route path={newGroupPath()} component={GroupEditPage} />
              <Route path={groupPath(":groupId")} component={GroupEditPage} />
              <Route path={groupsPath()} component={GroupListPage} />
              <Route path={jobsPath()} component={JobListPage} />
              <Route
                path={aclHistoryPath(":objectId")}
                component={ACLHistoryPage}
              />
              <Route path={aclPath(":objectId")} component={ACLEditPage} />
              <Route path={newUserPath()} component={UserEditPage} />
              <Route path={userPath(":userId")} component={UserEditPage} />
              <Route path={usersPath()} component={UserListPage} />
              <Route path={newRolePath()} component={RoleEditPage} />
              <Route path={rolePath(":roleId")} component={RoleEditPage} />
              <Route path={rolesPath()} component={RoleListPage} />
              <Route exact path={topPath()} component={DashboardPage} />
              <Route component={NotFoundErrorPage} />
            </Switch>
          </Route>
        </Switch>
      </ErrorHandler>
    </Router>
  );
};
