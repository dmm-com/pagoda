const basePath = "/new-ui/";

export const loginPath = () => "/auth/login/";
export const topPath = () => basePath;
export const advancedSearchPath = () => basePath + "advanced_search";
export const jobsPath = () => basePath + "jobs";
export const aclPath = (entityId: number | string) =>
  basePath + `acl/${entityId}`;
export const searchPath = () => basePath + "search";

// entris
export const newEntryPath = (entityId: number | string) =>
  basePath + `entities/${entityId}/entries/new`;
export const showEntryPath = (entryId: number | string) =>
  basePath + `entries/${entryId}/show`;
export const importEntriesPath = (entityId: number | string) =>
  basePath + `entities/${entityId}/entries/import`;
export const entityEntriesPath = (entityId: number | string) =>
  basePath + `entities/${entityId}/entries`;

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
