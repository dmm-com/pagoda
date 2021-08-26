import Cookies from "js-cookie";

// Get CSRF Token from Cookie set by Django
// see https://docs.djangoproject.com/en/3.2/ref/csrf/
export function getCsrfToken() {
  return Cookies.get("csrftoken");
}
