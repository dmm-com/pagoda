const basePath = "/new-ui/";

export const loginPath = () => "/auth/login/";
export const topPath = () => basePath;
export const advancedSearchPath = () => basePath + "advanced_search";
export const advancedSearchResultPath = () =>
  basePath + "advanced_search_result";
export const jobsPath = () => basePath + "jobs";
export const aclPath = (entityId: number | string) =>
  basePath + `acl/${entityId}`;
export const searchPath = () => basePath + "search";

// entris
export const newEntryPath = (entityId: number | string) =>
  basePath + `entities/${entityId}/entries/new`;
export const copyEntryPath = (
  entityId: number | string,
  entryId: number | string
) => basePath + `entities/${entityId}/entries/${entryId}/copy`;
export const entryDetailsPath = (
  entityId: number | string,
  entryId: number | string
) => basePath + `entities/${entityId}/entries/${entryId}/details`;
export const entryEditPath = (
  entityId: number | string,
  entryId: number | string
) => basePath + `entities/${entityId}/entries/${entryId}/edit`;
export const importEntriesPath = (entityId: number | string) =>
  basePath + `entities/${entityId}/entries/import`;
export const entityEntriesPath = (entityId: number | string) =>
  basePath + `entities/${entityId}/entries`;
export const restoreEntryPath = (entityId: number | string) =>
  basePath + `entities/${entityId}/restore`;
export const showEntryHistoryPath = (entryId: number | string) =>
  basePath + `entries/${entryId}/history`;

// entities
export const entityHistoryPath = (entityId: number | string) =>
  basePath + `entities/${entityId}/history`;
export const newEntityPath = () => basePath + "entities/new";
export const importEntitiesPath = () => basePath + "entities/import";
export const entityPath = (entityId: number | string) =>
  basePath + `entities/${entityId}`;
export const entitiesPath = () => basePath + "entities";

// groups
export const newGroupPath = () => basePath + "groups/new";
export const importGroupsPath = () => basePath + "groups/import";
export const groupPath = (groupId: number | string) =>
  basePath + `groups/${groupId}`;
export const groupsPath = () => basePath + "groups";

// users
export const newUserPath = () => basePath + "users/new";
export const importUsersPath = () => basePath + "users/import";
export const passwordPath = (userId: number | string) =>
  basePath + `users/${userId}/password`;
export const userPath = (userId: number | string) =>
  basePath + `users/${userId}`;
export const usersPath = () => basePath + "users";
