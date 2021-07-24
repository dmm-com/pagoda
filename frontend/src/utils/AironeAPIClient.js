import { getCsrfToken } from "./DjangoUtils";

export function getEntity(entityId) {
  return new Promise((resolve, _) => {
    resolve({
      name: "",
      note: "",
      attributes: [],
    });
  });
}

export function getEntities() {
  return fetch("/entity/api/v1/get_entities");
}

export function getEntityHistory(entityId) {
  return fetch(`/entity/api/v2/history/${entityId}`);
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
export function createEntity(name, note, attrs) {
  return fetch(`/entity/do_create`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      name: name,
      note: note,
      is_toplevel: false,
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

// FIXME implement internal API then call it
export function getUsers() {
  return new Promise((resolve, _) => {
    resolve([
      {
        id: 1,
        name: "test",
        email: "test@example.com",
        created_at: "",
      },
    ]);
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

// FIXME implement internal API then call it
export function getJobs() {
  return new Promise((resolve, _) => {
    resolve([
      {
        id: 1,
        entry: "entry1",
        operation: "作成",
        status: "完了",
        duration: "1s",
        created_at: "1st Jan 0:00pm",
        note: "",
      },
    ]);
  });
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
