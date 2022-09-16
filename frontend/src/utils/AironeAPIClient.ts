import Cookies from "js-cookie";
import fileDownload from "js-file-download";

// Get CSRF Token from Cookie set by Django
// see https://docs.djangoproject.com/en/3.2/ref/csrf/
function getCsrfToken(): string {
  return Cookies.get("csrftoken");
}

export function postLogin(formData: FormData): Promise<Response> {
  return fetch(`/auth/login/?next=${formData.get("next")}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: formData,
    redirect: "manual",
  });
}

export function postLogout(): Promise<Response> {
  return fetch("/auth/logout/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
  });
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

// FIXME unimplemented
export function getEntryHistory({}: number): Promise<object> {
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

export function restoreEntry(entryId: number): Promise<Response> {
  return fetch(`/entry/do_restore/${entryId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({}),
  });
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
  return fetch("/api/v1/user/access_token", {
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

export function rerunJob(jobId: number): Promise<Response> {
  return fetch(`/api/v1/job/run/${jobId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
  });
}

export function cancelJob(jobId: number): Promise<Response> {
  return fetch(`/api/v1/job/`, {
    method: "DELETE",
    headers: {
      "X-CSRFToken": getCsrfToken(),
      "Content-Type": "application/json;charset=utf-8",
    },
    body: JSON.stringify({
      job_id: jobId,
    }),
  });
}

export function exportAdvancedSearchResults(
  entities: number[],
  attrinfo: object[],
  entryName: string,
  hasReferral: boolean,
  exportStyle: "yaml" | "csv"
): Promise<Response> {
  return fetch(`/dashboard/advanced_search_export`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
      "Content-Type": "application/json;charset=utf-8",
    },
    body: JSON.stringify({
      entities: entities,
      attrinfo: attrinfo,
      entry_name: entryName,
      has_referral: hasReferral,
      export_style: exportStyle,
    }),
  });
}
