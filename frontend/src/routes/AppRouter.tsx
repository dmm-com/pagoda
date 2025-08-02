import { FC, ReactNode } from "react";
import {
  createBrowserRouter,
  createRoutesFromElements,
  Outlet,
  Route,
  RouterProvider,
  useRouteError,
} from "react-router";

import { ACLHistoryPage } from "../pages/ACLHistoryPage";
import { AliasEntryListPage } from "../pages/AliasEntryListPage";
import { CategoryListPage } from "../pages/CategoryListPage";
import { EntryCopyPage } from "../pages/EntryCopyPage";
import { EntryDetailsPage } from "../pages/EntryDetailsPage";
import { EntryRestorePage } from "../pages/EntryRestorePage";
import { NotFoundErrorPage } from "../pages/NotFoundErrorPage";
import { RoleEditPage } from "../pages/RoleEditPage";
import { RoleListPage } from "../pages/RoleListPage";

import { Header } from "components/common/Header";
import { ACLEditPage } from "pages/ACLEditPage";
import { AdvancedSearchPage } from "pages/AdvancedSearchPage";
import { AdvancedSearchResultsPage } from "pages/AdvancedSearchResultsPage";
import { CategoryEditPage } from "pages/CategoryEditPage";
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
import {
  aclHistoryPath,
  aclPath,
  advancedSearchPath,
  advancedSearchResultPath,
  copyEntryPath,
  editCategoryPath,
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
  listAliasPath,
  listCategoryPath,
  loginPath,
  newCategoryPath,
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
} from "routes/Routes";

// re-throw error to be caught by the root error boundary
const ErrorBridge: FC = () => {
  throw useRouteError();
};

interface Props {
  customRoutes?: {
    path: string;
    element: ReactNode;
  }[];
}

export const AppRouter: FC<Props> = ({ customRoutes }) => {
  const router = createBrowserRouter(
    createRoutesFromElements(
      <Route errorElement={<ErrorBridge />}>
        <Route path={loginPath()} element={<LoginPage />} />
        <Route
          path="/"
          element={
            <>
              <Header />
              <Outlet />
            </>
          }
        >
          {customRoutes &&
            customRoutes.map((r) => (
              <Route key={r.path} path={r.path} element={r.element} />
            ))}

          <Route path={newCategoryPath()} element={<CategoryEditPage />} />
          <Route
            path={editCategoryPath(":categoryId")}
            element={<CategoryEditPage />}
          />
          <Route path={listCategoryPath()} element={<CategoryListPage />} />
          <Route path={advancedSearchPath()} element={<AdvancedSearchPage />} />
          <Route
            path={advancedSearchResultPath()}
            element={<AdvancedSearchResultsPage />}
          />
          <Route path={newEntryPath(":entityId")} element={<EntryEditPage />} />
          <Route
            path={copyEntryPath(":entityId", ":entryId")}
            element={<EntryCopyPage />}
          />
          <Route
            path={entryDetailsPath(":entityId", ":entryId")}
            element={<EntryDetailsPage />}
          />
          <Route
            path={restoreEntryPath(":entityId")}
            element={<EntryRestorePage />}
          />
          <Route
            path={entryEditPath(":entityId", ":entryId")}
            element={<EntryEditPage />}
          />
          <Route
            path={showEntryHistoryPath(":entityId", ":entryId")}
            element={<EntryHistoryListPage />}
          />
          <Route
            path={entityEntriesPath(":entityId")}
            element={<EntryListPage />}
          />
          <Route
            path={entityHistoryPath(":entityId")}
            element={<EntityHistoryPage />}
          />
          <Route
            path={listAliasPath(":entityId")}
            element={<AliasEntryListPage />}
          />
          <Route path={newEntityPath()} element={<EntityEditPage />} />
          <Route
            path={editEntityPath(":entityId")}
            element={<EntityEditPage />}
          />
          <Route path={entitiesPath()} element={<EntityListPage />} />
          <Route path={newTriggerPath()} element={<TriggerEditPage />} />
          <Route
            path={editTriggerPath(":triggerId")}
            element={<TriggerEditPage />}
          />
          <Route path={triggersPath()} element={<TriggerListPage />} />
          <Route path={newGroupPath()} element={<GroupEditPage />} />
          <Route path={groupPath(":groupId")} element={<GroupEditPage />} />
          <Route path={groupsPath()} element={<GroupListPage />} />
          <Route path={jobsPath()} element={<JobListPage />} />
          <Route
            path={aclHistoryPath(":objectId")}
            element={<ACLHistoryPage />}
          />
          <Route path={aclPath(":objectId")} element={<ACLEditPage />} />
          <Route path={newUserPath()} element={<UserEditPage />} />
          <Route path={userPath(":userId")} element={<UserEditPage />} />
          <Route path={usersPath()} element={<UserListPage />} />
          <Route path={newRolePath()} element={<RoleEditPage />} />
          <Route path={rolePath(":roleId")} element={<RoleEditPage />} />
          <Route path={rolesPath()} element={<RoleListPage />} />
          <Route path={topPath()} element={<DashboardPage />} />
          <Route path="*" element={<NotFoundErrorPage />} />
        </Route>
      </Route>,
    ),
  );

  return <RouterProvider router={router} />;
};
