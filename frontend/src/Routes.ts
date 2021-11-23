const basePath = "/new-ui/";

export const topPath = () => basePath;
export const advancedSearchPath = () => basePath + "advanced_search";
export const jobsPath = () => basePath + "jobs";
export const aclPath = (entityId) => basePath + `acl/${entityId}`;
export const searchPath = () => basePath + "search";

// entris
export const newEntryPath = (entityId) =>
  basePath + `entities/${entityId}/entries/new`;
export const showEntryPath = (entryId) => basePath + `entries/${entryId}/show`;
export const importEntriesPath = (entityId) =>
  basePath + `entities/${entityId}/entries/import`;
export const entityEntriesPath = (entityId) =>
  basePath + `entities/${entityId}/entries`;

// entities
export const entityHistoryPath = (entityId) =>
  basePath + `entities/${entityId}/history`;
export const newEntityPath = () => basePath + "entities/new";
export const importEntitiesPath = () => basePath + "entities/import";
export const entityPath = (entityId) => basePath + `entities/${entityId}`;
export const entitiesPath = () => basePath + "entities";

// groups
export const newGroupPath = () => basePath + "groups/new";
export const importGroupsPath = () => basePath + "groups/import";
export const groupPath = (groupId) => basePath + `groups/${groupId}`;
export const groupsPath = () => basePath + "groups";

// users
export const newUserPath = () => basePath + "users/new";
export const importUsersPath = () => basePath + "users/import";
export const passwordPath = (userId) => basePath + `users/${userId}/password`;
export const userPath = (userId) => basePath + `users/${userId}`;
export const usersPath = () => basePath + "users";
