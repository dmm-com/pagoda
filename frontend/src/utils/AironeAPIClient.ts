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
