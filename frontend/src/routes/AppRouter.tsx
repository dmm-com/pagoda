import { FC, Suspense, lazy, ReactNode } from "react";
import {
  createBrowserRouter,
  createRoutesFromElements,
  Outlet,
  Route,
  RouterProvider,
  useRouteError,
} from "react-router";

import { NotFoundErrorPage } from "../pages/NotFoundErrorPage";

import { EntityAwareRoute } from "./EntityAwareRoute";

import { Header } from "components/common/Header";
import { Loading } from "components/common/Loading";
import { Plugin } from "plugins";
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

// Each page component is code-split and loaded on demand
const ACLHistoryPage = lazy(() =>
  import("pages/ACLHistoryPage").then((m) => ({
    default: m.ACLHistoryPage,
  })),
);
const ACLEditPage = lazy(() =>
  import("pages/ACLEditPage").then((m) => ({ default: m.ACLEditPage })),
);
const AdvancedSearchPage = lazy(() =>
  import("pages/AdvancedSearchPage").then((m) => ({
    default: m.AdvancedSearchPage,
  })),
);
const AdvancedSearchResultsPage = lazy(() =>
  import("pages/AdvancedSearchResultsPage").then((m) => ({
    default: m.AdvancedSearchResultsPage,
  })),
);
const AliasEntryListPage = lazy(() =>
  import("pages/AliasEntryListPage").then((m) => ({
    default: m.AliasEntryListPage,
  })),
);
const CategoryEditPage = lazy(() =>
  import("pages/CategoryEditPage").then((m) => ({
    default: m.CategoryEditPage,
  })),
);
const CategoryListPage = lazy(() =>
  import("pages/CategoryListPage").then((m) => ({
    default: m.CategoryListPage,
  })),
);
const DashboardPage = lazy(() =>
  import("pages/DashboardPage").then((m) => ({ default: m.DashboardPage })),
);
const EntryCopyPage = lazy(() =>
  import("pages/EntryCopyPage").then((m) => ({ default: m.EntryCopyPage })),
);
const EntryDetailsPage = lazy(() =>
  import("pages/EntryDetailsPage").then((m) => ({
    default: m.EntryDetailsPage,
  })),
);
const EntryEditPage = lazy(() =>
  import("pages/EntryEditPage").then((m) => ({ default: m.EntryEditPage })),
);
const EntryHistoryListPage = lazy(() =>
  import("pages/EntryHistoryListPage").then((m) => ({
    default: m.EntryHistoryListPage,
  })),
);
const EntryListPage = lazy(() =>
  import("pages/EntryListPage").then((m) => ({ default: m.EntryListPage })),
);
const EntryRestorePage = lazy(() =>
  import("pages/EntryRestorePage").then((m) => ({
    default: m.EntryRestorePage,
  })),
);
const EntityEditPage = lazy(() =>
  import("pages/EntityEditPage").then((m) => ({ default: m.EntityEditPage })),
);
const EntityHistoryPage = lazy(() =>
  import("pages/EntityHistoryPage").then((m) => ({
    default: m.EntityHistoryPage,
  })),
);
const EntityListPage = lazy(() =>
  import("pages/EntityListPage").then((m) => ({ default: m.EntityListPage })),
);
const GroupEditPage = lazy(() =>
  import("pages/GroupEditPage").then((m) => ({ default: m.GroupEditPage })),
);
const GroupListPage = lazy(() =>
  import("pages/GroupListPage").then((m) => ({ default: m.GroupListPage })),
);
const JobListPage = lazy(() =>
  import("pages/JobListPage").then((m) => ({ default: m.JobListPage })),
);
const LoginPage = lazy(() =>
  import("pages/LoginPage").then((m) => ({ default: m.LoginPage })),
);
const RoleEditPage = lazy(() =>
  import("pages/RoleEditPage").then((m) => ({ default: m.RoleEditPage })),
);
const RoleListPage = lazy(() =>
  import("pages/RoleListPage").then((m) => ({ default: m.RoleListPage })),
);
const TriggerEditPage = lazy(() =>
  import("pages/TriggerEditPage").then((m) => ({
    default: m.TriggerEditPage,
  })),
);
const TriggerListPage = lazy(() =>
  import("pages/TriggerListPage").then((m) => ({
    default: m.TriggerListPage,
  })),
);
const UserEditPage = lazy(() =>
  import("pages/UserEditPage").then((m) => ({ default: m.UserEditPage })),
);
const UserListPage = lazy(() =>
  import("pages/UserListPage").then((m) => ({ default: m.UserListPage })),
);

// re-throw error to be caught by the root error boundary
const ErrorBridge: FC = () => {
  throw useRouteError();
};

interface Props {
  customRoutes?: {
    path: string;
    element: ReactNode;
  }[];
  pluginMap?: Map<string, Plugin>;
}

export const AppRouter: FC<Props> = ({
  customRoutes,
  pluginMap = new Map(),
}) => {
  const router = createBrowserRouter(
    createRoutesFromElements(
      <Route errorElement={<ErrorBridge />}>
        <Route
          path={loginPath()}
          element={
            <Suspense fallback={<Loading />}>
              <LoginPage />
            </Suspense>
          }
        />
        <Route
          path="/"
          element={
            <>
              <Header />
              {/* page chunks resolved by the routes below are shown here */}
              <Suspense fallback={<Loading />}>
                <Outlet />
              </Suspense>
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
            element={
              <EntityAwareRoute
                pageType="entry.list"
                defaultComponent={EntryListPage}
                pluginMap={pluginMap}
              />
            }
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
