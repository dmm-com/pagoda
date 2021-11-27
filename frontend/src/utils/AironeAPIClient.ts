import Cookies from "js-cookie";
import fileDownload from "js-file-download";

// Get CSRF Token from Cookie set by Django
// see https://docs.djangoproject.com/en/3.2/ref/csrf/
function getCsrfToken(): string {
  return Cookies.get("csrftoken");
}

export function getEntity(entityId: number): Promise<Response> {
  return fetch(`/entity/api/v2/entities/${entityId}`);
}

export function getEntities(): Promise<Response> {
  return fetch("/entity/api/v1/get_entities");
}

export function getEntityHistory(entityId: number): Promise<Response> {
  return fetch(`/entity/api/v2/history/${entityId}`);
}

// NOTE it calls non-API endpoint
export function downloadExportedEntities(filename: string): Promise<void> {
  return fetch("/entity/export/")
    .then((resp) => resp.blob())
    .then((blob) => fileDownload(blob, filename));
}

export function importEntities(formData: FormData): Promise<Response> {
  return fetch(`/dashboard/do_import/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: formData,
  });
}

export function getEntityAttrs(entityIds: number[]): Promise<Response> {
  return fetch(`/api/v1/entity/attrs/${entityIds.join(",")}`);
}

export function getEntry(entryId: number): Promise<Response> {
  return fetch(`/entry/api/v2/${entryId}`);
}

export function getEntries(
  entityId: number,
  isActive = true
): Promise<Response> {
  const isActiveParam = isActive ? "True" : "False";
  return fetch(
    `/entry/api/v1/get_entries/${entityId}?is_active=${isActiveParam}`
  );
}

export function importEntries(
  entityId: number,
  formData: FormData
): Promise<Response> {
  return fetch(`/entry/do_import/${entityId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: formData,
  });
}

// FIXME it should be better to implement a new internal API than this
export function searchEntries(
  entityIds: number[] = [],
  entryName = "",
  attrInfo: object[] = [],
  entryLimit = 99999
): Promise<Response> {
  return fetch(`/api/v1/entry/search`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
      "Content-Type": "application/json;charset=utf-8",
    },
    body: JSON.stringify({
      entities: entityIds,
      entry_name: entryName,
      attrinfo: attrInfo,
      entry_limit: entryLimit,
    }),
  });
}

export function getACL(objectId: number): Promise<Response> {
  return fetch(`/acl/api/v2/acls/${objectId}`);
}

export function updateACL(
  objectId: number,
  name: string,
  objectType: string,
  isPublic: boolean,
  defaultPermission: number,
  acl: object
): Promise<Response> {
  return fetch(`/acl/api/v2/acls/${objectId}`, {
    method: "PUT",
    headers: {
      "X-CSRFToken": getCsrfToken(),
      "Content-Type": "application/json;charset=utf-8",
    },
    body: JSON.stringify({
      name: name,
      objtype: objectType,
      is_public: isPublic,
      default_permission: defaultPermission,
      acl: acl,
    }),
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function createEntity(
  name: string,
  note: string,
  isTopLevel: boolean,
  attrs: object[]
): Promise<Response> {
  return fetch(`/entity/do_create`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      name: name,
      note: note,
      is_toplevel: isTopLevel,
      attrs: attrs,
    }),
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function updateEntity(
  entityId: number,
  name: string,
  note: string,
  isTopLevel: boolean,
  attrs: object[]
): Promise<Response> {
  return fetch(`/entity/do_edit/${entityId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      name: name,
      note: note,
      is_toplevel: isTopLevel,
      attrs: attrs,
    }),
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function deleteEntity(entityId: number): Promise<Response> {
  return fetch(`/entity/do_delete/${entityId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({}),
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function createEntry(
  entityId: number,
  name: string,
  attrs: object[]
): Promise<Response> {
  return fetch(`/entry/do_create/${entityId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      entry_name: name,
      attrs: attrs,
    }),
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function deleteEntry(entryId: number): Promise<Response> {
  return fetch(`/entry/do_delete/${entryId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({}),
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function restoreEntry(entryId: number): Promise<Response> {
  return fetch(`/entry/do_restore/${entryId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({}),
  });
}

export function copyEntry(entryId: number, entries: string): Promise<Response> {
  return fetch(`/entry/do_copy/${entryId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      entries: entries,
    }),
  });
}

export function getEntryHistory(entryId: number): Promise<object> {
  return new Promise((resolve) => {
    resolve([
      {
        attr_name: "test",
        prev: {
          created_user: "admin",
          created_time: new Date().toDateString(),
          value: "before",
        },
        curr: {
          created_user: "admin",
          created_time: new Date().toDateString(),
          value: "after",
        },
      },
    ]);
  });
}

export function getReferredEntries(entryId: number): Promise<Response> {
  return fetch(`/entry/api/v1/get_referrals/${entryId}`);
}

export function exportEntries(
  entityId: number,
  format: string
): Promise<Response> {
  return fetch(`/entry/export/${entityId}?format=${format}`);
}

// FIXME implement internal API then call it
export function getUser(userId: number): Promise<Response> {
  return fetch(`/user/api/v2/users/${userId}`);
}

export function getUsers(): Promise<Response> {
  return fetch("/user/api/v2/users");
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function createUser(
  name: string,
  email: string,
  password: string,
  isSuperuser: boolean,
  tokenLifetime: number
): Promise<Response> {
  return fetch(`/user/do_create`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      name: name,
      email: email,
      passwd: password,
      is_superuser: isSuperuser,
      token_lifetime: String(tokenLifetime),
    }),
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function updateUser(
  userId: number,
  name: string,
  email: string,
  isSuperuser: boolean,
  tokenLifetime: number
): Promise<Response> {
  return fetch(`/user/do_edit/${userId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      name: name,
      email: email,
      is_superuser: isSuperuser,
      token_lifetime: String(tokenLifetime),
    }),
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function deleteUser(userId: number): Promise<Response> {
  return fetch(`/user/do_delete/${userId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({}),
  });
}

// NOTE it calls non-API endpoint
export function downloadExportedUsers(filename: string): Promise<void> {
  return fetch("/user/export/")
    .then((resp) => resp.blob())
    .then((blob) => fileDownload(blob, filename));
}

// FIXME implement V2 API
export function refreshAccessToken(): Promise<Response> {
  return fetch("/api/v1/user/access_token/", {
    method: "PUT",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function updateUserPassword(
  userId: number,
  oldPassword: string,
  newPassword: string,
  checkPassword: string
): Promise<Response> {
  return fetch(`/user/do_edit_passwd/${userId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      old_passwd: oldPassword,
      new_passwd: newPassword,
      chk_passwd: checkPassword,
    }),
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function updateUserPasswordAsSuperuser(
  userId: number,
  newPassword: string,
  checkPassword: string
): Promise<Response> {
  return fetch(`/user/do_su_edit_passwd/${userId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      new_passwd: newPassword,
      chk_passwd: checkPassword,
    }),
  });
}

// FIXME implement internal API then call it
export function getGroups(): Promise<Response> {
  return fetch("/group/api/v2/groups");
}

export function getGroup(groupId: number): Promise<Response> {
  return fetch(`/group/api/v2/groups/${groupId}`);
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function createGroup(
  name: string,
  members: number[]
): Promise<Response> {
  return fetch(`/group/do_create`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      name: name,
      users: members,
    }),
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function updateGroup(
  groupId: number,
  name: string,
  members: number[]
): Promise<Response> {
  return fetch(`/group/do_edit/${groupId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      name: name,
      users: members,
    }),
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function deleteGroup(groupId: number): Promise<Response> {
  return fetch(`/group/do_delete/${groupId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({}),
  });
}

// NOTE it calls non-API endpoint
export function downloadExportedGroups(filename: string): Promise<void> {
  return fetch("/group/export/")
    .then((resp) => resp.blob())
    .then((blob) => fileDownload(blob, filename));
}

export function importGroups(formData: FormData): Promise<Response> {
  return fetch(`/group/do_import/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: formData,
  });
}

export function getJobs(noLimit = 0): Promise<Response> {
  return fetch(`/job/api/v2/jobs?nolimit=${noLimit}`);
}

export function getRecentJobs(): Promise<Response> {
  return fetch(`/api/v1/job/`);
}

export function getWebhooks(entityId: number): Promise<Response> {
  return fetch(`/webhook/api/v2/${entityId}`);
}

export function setWebhook(
  entityId: number,
  request_parameter: object
): Promise<Response> {
  return fetch(`/webhook/api/v1/set/${entityId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify(request_parameter),
  });
}

export function deleteWebhook(webhookId: number): Promise<Response> {
  return fetch(`/webhook/api/v1/del/${webhookId}`, {
    method: "DELETE",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
  });
}
