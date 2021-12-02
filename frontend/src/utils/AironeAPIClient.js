import Cookies from "js-cookie";
import fileDownload from "js-file-download";

// Get CSRF Token from Cookie set by Django
// see https://docs.djangoproject.com/en/3.2/ref/csrf/
function getCsrfToken() {
  return Cookies.get("csrftoken");
}

export function getEntity(entityId) {
  return fetch(`/entity/api/v2/entities/${entityId}`);
}

export function getEntities() {
  return fetch("/entity/api/v1/get_entities");
}

export function getEntityHistory(entityId) {
  return fetch(`/entity/api/v2/history/${entityId}`);
}

// NOTE it calls non-API endpoint
export function downloadExportedEntities(filename) {
  return fetch("/entity/export/")
    .then((resp) => resp.blob())
    .then((blob) => fileDownload(blob, filename));
}

export function importEntities(formData) {
  return fetch(`/dashboard/do_import/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: formData,
  });
}

export function getEntityAttrs(entityIds) {
  return fetch(`/api/v1/entity/attrs/${entityIds.join(",")}`);
}

export function getEntry(entryId) {
  return fetch(`/entry/api/v2/${entryId}`);
}

export function getEntries(entityId, isActive = true) {
  const isActiveParam = isActive ? "True" : "False";
  return fetch(
    `/entry/api/v1/get_entries/${entityId}?is_active=${isActiveParam}`
  );
}

export function getAttrReferrals(attr_id) {
  return fetch(`/entry/api/v1/get_attr_referrals/${attr_id}/`);
}

export function importEntries(entityId, formData) {
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
  entityIds = [],
  entryName = "",
  attrInfo = [],
  entryLimit = 99999
) {
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

export function getACL(objectId) {
  return new Promise((resolve, _) => {
    resolve({
      object: {
        name: "entity1",
        is_public: true,
      },
      acltypes: [
        {
          id: 1,
          name: "Nothing",
        },
        {
          id: 2,
          name: "Full Controllable",
        },
      ],
      members: [
        {
          name: "admin",
          current_permission: 1,
        },
      ],
    });
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function createEntity(name, note, isTopLevel, attrs) {
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
export function updateEntity(entityId, name, note, isTopLevel, attrs) {
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
export function deleteEntity(entityId) {
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
export function createEntry(entityId, name, attrs) {
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

export function updateEntry(entryId, name, attrs) {
  return fetch(`/entry/do_edit/${entryId}/`, {
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
export function deleteEntry(entryId) {
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
export function restoreEntry(entryId) {
  return fetch(`/entry/do_restore/${entryId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({}),
  });
}

export function copyEntry(entryId, entries) {
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

export function getEntryHistory(entryId) {
  return new Promise((resolve, _) => {
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

export function getReferredEntries(entryId) {
  return fetch(`/entry/api/v1/get_referrals/${entryId}`);
}

export function exportEntries(entityId, format) {
  return fetch(`/entry/export/${entityId}?format=${format}`);
}

// FIXME implement internal API then call it
export function getUser(userId) {
  return fetch(`/user/api/v2/users/${userId}`);
}

export function getUsers() {
  return fetch("/user/api/v2/users");
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function createUser(name, email, password, isSuperuser, tokenLifetime) {
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
export function updateUser(userId, name, email, isSuperuser, tokenLifetime) {
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
export function deleteUser(userId) {
  return fetch(`/user/do_delete/${userId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({}),
  });
}

// NOTE it calls non-API endpoint
export function downloadExportedUsers(filename) {
  return fetch("/user/export/")
    .then((resp) => resp.blob())
    .then((blob) => fileDownload(blob, filename));
}

// FIXME implement V2 API
export function refreshAccessToken() {
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
  userId,
  oldPassword,
  newPassword,
  checkPassword
) {
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
  userId,
  newPassword,
  checkPassword
) {
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
export function getGroups() {
  return fetch("/group/api/v2/groups");
}

export function getGroup(groupId) {
  return fetch(`/group/api/v2/groups/${groupId}`);
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function createGroup(name, members) {
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
export function updateGroup(groupId, name, members) {
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
export function deleteGroup(groupId) {
  return fetch(`/group/do_delete/${groupId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({}),
  });
}

// NOTE it calls non-API endpoint
export function downloadExportedGroups(filename) {
  return fetch("/group/export/")
    .then((resp) => resp.blob())
    .then((blob) => fileDownload(blob, filename));
}

export function importGroups(formData) {
  return fetch(`/group/do_import/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: formData,
  });
}

export function getJobs(noLimit = 0) {
  return fetch(`/job/api/v2/jobs?nolimit=${noLimit}`);
}

export function getRecentJobs() {
  return fetch(`/api/v1/job/`);
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function updateACL(objectId, objectType, acl, defaultPermission) {
  return fetch(`/acl/set`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      object_id: objectId,
      object_type: objectType,
      acl: acl,
      default_permission: defaultPermission,
    }),
  });
}

export function getWebhooks(entityId) {
  return fetch(`/webhook/api/v2/${entityId}`);
}

export function setWebhook(entityId, request_parameter) {
  return fetch(`/webhook/api/v1/set/${entityId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify(request_parameter),
  });
}

export function deleteWebhook(webhookId) {
  return fetch(`/webhook/api/v1/del/${webhookId}`, {
    method: "DELETE",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
  });
}
