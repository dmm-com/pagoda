import Cookies from "js-cookie";

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

export function getEntityAttrs(
  entityIds: number[],
  searchAllEntities = false
): Promise<Response> {
  // NOTE "," is a magic means specifying all the attributes
  const path = searchAllEntities ? "," : entityIds.join(",");
  return fetch(`/api/v1/entity/attrs/${path}`);
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
