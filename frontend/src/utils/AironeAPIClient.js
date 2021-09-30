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
  return new Promise((resolve, _) => {
    resolve([
      {
        user: {
          username: "test",
        },
        operation: (1 << 0) + (1 << 3), // ADD_ENTITY
        details: [
          {
            operation: (1 << 1) + (1 << 4), // MOD_ATTR
            target_obj: "test_attr",
            text: "mod test_attr",
          },
        ],
        time: "2021-01-01 00:00:00",
      },
    ]);
  });
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

export function getEntry(entityId, entryId) {
  return new Promise((resolve, _) => {
    resolve({
      name: "test",
      attributes: [
        {
          name: "a1",
          value: "aaa",
        },
      ],
    });
  });
}

export function getEntries(entityId) {
  return fetch(`/entry/api/v1/get_entries/${entityId}`);
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

export function getAdvancedSearchResults() {
  return new Promise((resolve, _) => {
    resolve([
      {
        name: "test",
        attr1: "val1",
        attr2: "val2",
      },
    ]);
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
  return new Promise((resolve, _) => {
    resolve([
      {
        id: 1,
        name: "test",
        members: [
          {
            name: "user1",
          },
          {
            name: "user2",
          },
        ],
      },
    ]);
  });
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function deleteGroup(groupId) {
  return fetch(`/gruop/do_delete/${groupId}`, {
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
