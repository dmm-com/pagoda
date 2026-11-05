# UserApi

All URIs are relative to _http://localhost_

| Method                                                                                    | HTTP request                                 | Description |
| ----------------------------------------------------------------------------------------- | -------------------------------------------- | ----------- |
| [**userApiV2ActivityRetrieve**](UserApi.md#userapiv2activityretrieve)                     | **GET** /user/api/v2/{id}/activity           |             |
| [**userApiV2AuthPartialUpdate**](UserApi.md#userapiv2authpartialupdate)                   | **PATCH** /user/api/v2/{id}/auth             |             |
| [**userApiV2AuthUpdate**](UserApi.md#userapiv2authupdate)                                 | **PUT** /user/api/v2/{id}/auth               |             |
| [**userApiV2CoUserTokenRefresh**](UserApi.md#userapiv2cousertokenrefresh)                 | **POST** /user/api/v2/{id}/token/            |             |
| [**userApiV2Create**](UserApi.md#userapiv2create)                                         | **POST** /user/api/v2/                       |             |
| [**userApiV2Destroy**](UserApi.md#userapiv2destroy)                                       | **DELETE** /user/api/v2/{id}/                |             |
| [**userApiV2EditPasswdPartialUpdate**](UserApi.md#userapiv2editpasswdpartialupdate)       | **PATCH** /user/api/v2/{id}/edit_passwd      |             |
| [**userApiV2EditPasswdUpdate**](UserApi.md#userapiv2editpasswdupdate)                     | **PUT** /user/api/v2/{id}/edit_passwd        |             |
| [**userApiV2ExportCreate**](UserApi.md#userapiv2exportcreate)                             | **POST** /user/api/v2/export                 |             |
| [**userApiV2ExportCreate2**](UserApi.md#userapiv2exportcreate2)                           | **POST** /user/api/v2/export/                |             |
| [**userApiV2ImportCreate**](UserApi.md#userapiv2importcreate)                             | **POST** /user/api/v2/import/                |             |
| [**userApiV2List**](UserApi.md#userapiv2list)                                             | **GET** /user/api/v2/                        |             |
| [**userApiV2MeRetrieve**](UserApi.md#userapiv2meretrieve)                                 | **GET** /user/api/v2/me                      |             |
| [**userApiV2PasswordResetConfirmCreate**](UserApi.md#userapiv2passwordresetconfirmcreate) | **POST** /user/api/v2/password_reset/confirm |             |
| [**userApiV2PasswordResetCreate**](UserApi.md#userapiv2passwordresetcreate)               | **POST** /user/api/v2/password_reset         |             |
| [**userApiV2Retrieve**](UserApi.md#userapiv2retrieve)                                     | **GET** /user/api/v2/{id}/                   |             |
| [**userApiV2SuEditPasswdPartialUpdate**](UserApi.md#userapiv2sueditpasswdpartialupdate)   | **PATCH** /user/api/v2/{id}/su_edit_passwd   |             |
| [**userApiV2SuEditPasswdUpdate**](UserApi.md#userapiv2sueditpasswdupdate)                 | **PUT** /user/api/v2/{id}/su_edit_passwd     |             |
| [**userApiV2TokenRefresh**](UserApi.md#userapiv2tokenrefresh)                             | **POST** /user/api/v2/token/                 |             |
| [**userApiV2TokenRetrieve**](UserApi.md#userapiv2tokenretrieve)                           | **GET** /user/api/v2/token/                  |             |
| [**userApiV2Update**](UserApi.md#userapiv2update)                                         | **PUT** /user/api/v2/{id}/                   |             |

## userApiV2ActivityRetrieve

> UserActivity userApiV2ActivityRetrieve(id)

### Example

```ts
import { Configuration, UserApi } from "";
import type { UserApiV2ActivityRetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // number
    id: 56,
  } satisfies UserApiV2ActivityRetrieveRequest;

  try {
    const data = await api.userApiV2ActivityRetrieve(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name   | Type     | Description | Notes                     |
| ------ | -------- | ----------- | ------------------------- |
| **id** | `number` |             | [Defaults to `undefined`] |

### Return type

[**UserActivity**](UserActivity.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2AuthPartialUpdate

> UserAuth userApiV2AuthPartialUpdate(id, patchedUserAuth)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2AuthPartialUpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // number
    id: 56,
    // PatchedUserAuth (optional)
    patchedUserAuth: ...,
  } satisfies UserApiV2AuthPartialUpdateRequest;

  try {
    const data = await api.userApiV2AuthPartialUpdate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                | Type                                  | Description | Notes                     |
| ------------------- | ------------------------------------- | ----------- | ------------------------- |
| **id**              | `number`                              |             | [Defaults to `undefined`] |
| **patchedUserAuth** | [PatchedUserAuth](PatchedUserAuth.md) |             | [Optional]                |

### Return type

[**UserAuth**](UserAuth.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2AuthUpdate

> UserAuth userApiV2AuthUpdate(id, userAuth)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2AuthUpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // number
    id: 56,
    // UserAuth
    userAuth: ...,
  } satisfies UserApiV2AuthUpdateRequest;

  try {
    const data = await api.userApiV2AuthUpdate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name         | Type                    | Description | Notes                     |
| ------------ | ----------------------- | ----------- | ------------------------- |
| **id**       | `number`                |             | [Defaults to `undefined`] |
| **userAuth** | [UserAuth](UserAuth.md) |             |                           |

### Return type

[**UserAuth**](UserAuth.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2CoUserTokenRefresh

> UserToken userApiV2CoUserTokenRefresh(id, userToken)

Allow a parent user to refresh the token of their co-user.

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2CoUserTokenRefreshRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // number
    id: 56,
    // UserToken (optional)
    userToken: ...,
  } satisfies UserApiV2CoUserTokenRefreshRequest;

  try {
    const data = await api.userApiV2CoUserTokenRefresh(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name          | Type                      | Description | Notes                     |
| ------------- | ------------------------- | ----------- | ------------------------- |
| **id**        | `number`                  |             | [Defaults to `undefined`] |
| **userToken** | [UserToken](UserToken.md) |             | [Optional]                |

### Return type

[**UserToken**](UserToken.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2Create

> UserCreate userApiV2Create(userCreate)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2CreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // UserCreate
    userCreate: ...,
  } satisfies UserApiV2CreateRequest;

  try {
    const data = await api.userApiV2Create(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name           | Type                        | Description | Notes |
| -------------- | --------------------------- | ----------- | ----- |
| **userCreate** | [UserCreate](UserCreate.md) |             |       |

### Return type

[**UserCreate**](UserCreate.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **201**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2Destroy

> userApiV2Destroy(id)

### Example

```ts
import { Configuration, UserApi } from "";
import type { UserApiV2DestroyRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // number
    id: 56,
  } satisfies UserApiV2DestroyRequest;

  try {
    const data = await api.userApiV2Destroy(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name   | Type     | Description | Notes                     |
| ------ | -------- | ----------- | ------------------------- |
| **id** | `number` |             | [Defaults to `undefined`] |

### Return type

`void` (Empty response body)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description      | Response headers |
| ----------- | ---------------- | ---------------- |
| **204**     | No response body | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2EditPasswdPartialUpdate

> UserPassword userApiV2EditPasswdPartialUpdate(id, patchedUserPassword)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2EditPasswdPartialUpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // number
    id: 56,
    // PatchedUserPassword (optional)
    patchedUserPassword: ...,
  } satisfies UserApiV2EditPasswdPartialUpdateRequest;

  try {
    const data = await api.userApiV2EditPasswdPartialUpdate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                    | Type                                          | Description | Notes                     |
| ----------------------- | --------------------------------------------- | ----------- | ------------------------- |
| **id**                  | `number`                                      |             | [Defaults to `undefined`] |
| **patchedUserPassword** | [PatchedUserPassword](PatchedUserPassword.md) |             | [Optional]                |

### Return type

[**UserPassword**](UserPassword.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2EditPasswdUpdate

> UserPassword userApiV2EditPasswdUpdate(id, userPassword)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2EditPasswdUpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // number
    id: 56,
    // UserPassword
    userPassword: ...,
  } satisfies UserApiV2EditPasswdUpdateRequest;

  try {
    const data = await api.userApiV2EditPasswdUpdate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name             | Type                            | Description | Notes                     |
| ---------------- | ------------------------------- | ----------- | ------------------------- |
| **id**           | `number`                        |             | [Defaults to `undefined`] |
| **userPassword** | [UserPassword](UserPassword.md) |             |                           |

### Return type

[**UserPassword**](UserPassword.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2ExportCreate

> JobSerializers userApiV2ExportCreate()

### Example

```ts
import { Configuration, UserApi } from "";
import type { UserApiV2ExportCreateRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  try {
    const data = await api.userApiV2ExportCreate();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**JobSerializers**](JobSerializers.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **202**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2ExportCreate2

> JobSerializers userApiV2ExportCreate2()

### Example

```ts
import { Configuration, UserApi } from "";
import type { UserApiV2ExportCreate2Request } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  try {
    const data = await api.userApiV2ExportCreate2();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**JobSerializers**](JobSerializers.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **202**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2ImportCreate

> userApiV2ImportCreate(userImportChild)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2ImportCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // Array<UserImportChild>
    userImportChild: ...,
  } satisfies UserApiV2ImportCreateRequest;

  try {
    const data = await api.userApiV2ImportCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                | Type                     | Description | Notes |
| ------------------- | ------------------------ | ----------- | ----- |
| **userImportChild** | `Array<UserImportChild>` |             |       |

### Return type

`void` (Empty response body)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/yaml`
- **Accept**: Not defined

### HTTP response details

| Status code | Description      | Response headers |
| ----------- | ---------------- | ---------------- |
| **200**     | No response body | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2List

> PaginatedUserListList userApiV2List(ordering, page, search)

### Example

```ts
import { Configuration, UserApi } from "";
import type { UserApiV2ListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // string | Which field to use when ordering the results. (optional)
    ordering: ordering_example,
    // number | A page number within the paginated result set. (optional)
    page: 56,
    // string | A search term. (optional)
    search: search_example,
  } satisfies UserApiV2ListRequest;

  try {
    const data = await api.userApiV2List(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name         | Type     | Description                                    | Notes                                |
| ------------ | -------- | ---------------------------------------------- | ------------------------------------ |
| **ordering** | `string` | Which field to use when ordering the results.  | [Optional] [Defaults to `undefined`] |
| **page**     | `number` | A page number within the paginated result set. | [Optional] [Defaults to `undefined`] |
| **search**   | `string` | A search term.                                 | [Optional] [Defaults to `undefined`] |

### Return type

[**PaginatedUserListList**](PaginatedUserListList.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2MeRetrieve

> UserMe userApiV2MeRetrieve()

### Example

```ts
import { Configuration, UserApi } from "";
import type { UserApiV2MeRetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  try {
    const data = await api.userApiV2MeRetrieve();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**UserMe**](UserMe.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2PasswordResetConfirmCreate

> PasswordResetConfirm userApiV2PasswordResetConfirmCreate(passwordResetConfirm)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2PasswordResetConfirmCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // PasswordResetConfirm
    passwordResetConfirm: ...,
  } satisfies UserApiV2PasswordResetConfirmCreateRequest;

  try {
    const data = await api.userApiV2PasswordResetConfirmCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                     | Type                                            | Description | Notes |
| ------------------------ | ----------------------------------------------- | ----------- | ----- |
| **passwordResetConfirm** | [PasswordResetConfirm](PasswordResetConfirm.md) |             |       |

### Return type

[**PasswordResetConfirm**](PasswordResetConfirm.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2PasswordResetCreate

> PasswordReset userApiV2PasswordResetCreate(passwordReset)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2PasswordResetCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // PasswordReset
    passwordReset: ...,
  } satisfies UserApiV2PasswordResetCreateRequest;

  try {
    const data = await api.userApiV2PasswordResetCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name              | Type                              | Description | Notes |
| ----------------- | --------------------------------- | ----------- | ----- |
| **passwordReset** | [PasswordReset](PasswordReset.md) |             |       |

### Return type

[**PasswordReset**](PasswordReset.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2Retrieve

> UserRetrieve userApiV2Retrieve(id)

### Example

```ts
import { Configuration, UserApi } from "";
import type { UserApiV2RetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // number
    id: 56,
  } satisfies UserApiV2RetrieveRequest;

  try {
    const data = await api.userApiV2Retrieve(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name   | Type     | Description | Notes                     |
| ------ | -------- | ----------- | ------------------------- |
| **id** | `number` |             | [Defaults to `undefined`] |

### Return type

[**UserRetrieve**](UserRetrieve.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2SuEditPasswdPartialUpdate

> UserPasswordBySuperuser userApiV2SuEditPasswdPartialUpdate(id, patchedUserPasswordBySuperuser)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2SuEditPasswdPartialUpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // number
    id: 56,
    // PatchedUserPasswordBySuperuser (optional)
    patchedUserPasswordBySuperuser: ...,
  } satisfies UserApiV2SuEditPasswdPartialUpdateRequest;

  try {
    const data = await api.userApiV2SuEditPasswdPartialUpdate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                               | Type                                                                | Description | Notes                     |
| ---------------------------------- | ------------------------------------------------------------------- | ----------- | ------------------------- |
| **id**                             | `number`                                                            |             | [Defaults to `undefined`] |
| **patchedUserPasswordBySuperuser** | [PatchedUserPasswordBySuperuser](PatchedUserPasswordBySuperuser.md) |             | [Optional]                |

### Return type

[**UserPasswordBySuperuser**](UserPasswordBySuperuser.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2SuEditPasswdUpdate

> UserPasswordBySuperuser userApiV2SuEditPasswdUpdate(id, userPasswordBySuperuser)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2SuEditPasswdUpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // number
    id: 56,
    // UserPasswordBySuperuser
    userPasswordBySuperuser: ...,
  } satisfies UserApiV2SuEditPasswdUpdateRequest;

  try {
    const data = await api.userApiV2SuEditPasswdUpdate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                        | Type                                                  | Description | Notes                     |
| --------------------------- | ----------------------------------------------------- | ----------- | ------------------------- |
| **id**                      | `number`                                              |             | [Defaults to `undefined`] |
| **userPasswordBySuperuser** | [UserPasswordBySuperuser](UserPasswordBySuperuser.md) |             |                           |

### Return type

[**UserPasswordBySuperuser**](UserPasswordBySuperuser.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2TokenRefresh

> UserToken userApiV2TokenRefresh(userToken)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2TokenRefreshRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // UserToken (optional)
    userToken: ...,
  } satisfies UserApiV2TokenRefreshRequest;

  try {
    const data = await api.userApiV2TokenRefresh(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name          | Type                      | Description | Notes      |
| ------------- | ------------------------- | ----------- | ---------- |
| **userToken** | [UserToken](UserToken.md) |             | [Optional] |

### Return type

[**UserToken**](UserToken.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2TokenRetrieve

> UserToken userApiV2TokenRetrieve()

### Example

```ts
import { Configuration, UserApi } from "";
import type { UserApiV2TokenRetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  try {
    const data = await api.userApiV2TokenRetrieve();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**UserToken**](UserToken.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## userApiV2Update

> UserUpdate userApiV2Update(id, userUpdate)

### Example

```ts
import {
  Configuration,
  UserApi,
} from '';
import type { UserApiV2UpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new UserApi(config);

  const body = {
    // number
    id: 56,
    // UserUpdate
    userUpdate: ...,
  } satisfies UserApiV2UpdateRequest;

  try {
    const data = await api.userApiV2Update(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name           | Type                        | Description | Notes                     |
| -------------- | --------------------------- | ----------- | ------------------------- |
| **id**         | `number`                    |             | [Defaults to `undefined`] |
| **userUpdate** | [UserUpdate](UserUpdate.md) |             |                           |

### Return type

[**UserUpdate**](UserUpdate.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
