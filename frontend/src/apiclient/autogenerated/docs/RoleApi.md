# RoleApi

All URIs are relative to _http://localhost_

| Method                                                        | HTTP request                 | Description |
| ------------------------------------------------------------- | ---------------------------- | ----------- |
| [**roleApiV2Create**](RoleApi.md#roleapiv2create)             | **POST** /role/api/v2/       |             |
| [**roleApiV2Destroy**](RoleApi.md#roleapiv2destroy)           | **DELETE** /role/api/v2/{id} |             |
| [**roleApiV2ExportCreate**](RoleApi.md#roleapiv2exportcreate) | **POST** /role/api/v2/export |             |
| [**roleApiV2ImportCreate**](RoleApi.md#roleapiv2importcreate) | **POST** /role/api/v2/import |             |
| [**roleApiV2List**](RoleApi.md#roleapiv2list)                 | **GET** /role/api/v2/        |             |
| [**roleApiV2Retrieve**](RoleApi.md#roleapiv2retrieve)         | **GET** /role/api/v2/{id}    |             |
| [**roleApiV2Update**](RoleApi.md#roleapiv2update)             | **PUT** /role/api/v2/{id}    |             |

## roleApiV2Create

> RoleCreateUpdate roleApiV2Create(roleCreateUpdate)

### Example

```ts
import {
  Configuration,
  RoleApi,
} from '';
import type { RoleApiV2CreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new RoleApi(config);

  const body = {
    // RoleCreateUpdate
    roleCreateUpdate: ...,
  } satisfies RoleApiV2CreateRequest;

  try {
    const data = await api.roleApiV2Create(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                 | Type                                    | Description | Notes |
| -------------------- | --------------------------------------- | ----------- | ----- |
| **roleCreateUpdate** | [RoleCreateUpdate](RoleCreateUpdate.md) |             |       |

### Return type

[**RoleCreateUpdate**](RoleCreateUpdate.md)

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

## roleApiV2Destroy

> roleApiV2Destroy(id)

### Example

```ts
import { Configuration, RoleApi } from "";
import type { RoleApiV2DestroyRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new RoleApi(config);

  const body = {
    // number
    id: 56,
  } satisfies RoleApiV2DestroyRequest;

  try {
    const data = await api.roleApiV2Destroy(body);
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

## roleApiV2ExportCreate

> JobSerializers roleApiV2ExportCreate()

### Example

```ts
import { Configuration, RoleApi } from "";
import type { RoleApiV2ExportCreateRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new RoleApi(config);

  try {
    const data = await api.roleApiV2ExportCreate();
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

## roleApiV2ImportCreate

> Array&lt;RoleImportExportChild&gt; roleApiV2ImportCreate(roleImportExportChild)

### Example

```ts
import {
  Configuration,
  RoleApi,
} from '';
import type { RoleApiV2ImportCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new RoleApi(config);

  const body = {
    // Array<RoleImportExportChild>
    roleImportExportChild: ...,
  } satisfies RoleApiV2ImportCreateRequest;

  try {
    const data = await api.roleApiV2ImportCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                      | Type                           | Description | Notes |
| ------------------------- | ------------------------------ | ----------- | ----- |
| **roleImportExportChild** | `Array<RoleImportExportChild>` |             |       |

### Return type

[**Array&lt;RoleImportExportChild&gt;**](RoleImportExportChild.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/yaml`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## roleApiV2List

> Array&lt;Role&gt; roleApiV2List(ordering, search)

### Example

```ts
import { Configuration, RoleApi } from "";
import type { RoleApiV2ListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new RoleApi(config);

  const body = {
    // string | Which field to use when ordering the results. (optional)
    ordering: ordering_example,
    // string | A search term. (optional)
    search: search_example,
  } satisfies RoleApiV2ListRequest;

  try {
    const data = await api.roleApiV2List(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name         | Type     | Description                                   | Notes                                |
| ------------ | -------- | --------------------------------------------- | ------------------------------------ |
| **ordering** | `string` | Which field to use when ordering the results. | [Optional] [Defaults to `undefined`] |
| **search**   | `string` | A search term.                                | [Optional] [Defaults to `undefined`] |

### Return type

[**Array&lt;Role&gt;**](Role.md)

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

## roleApiV2Retrieve

> Role roleApiV2Retrieve(id)

### Example

```ts
import { Configuration, RoleApi } from "";
import type { RoleApiV2RetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new RoleApi(config);

  const body = {
    // number
    id: 56,
  } satisfies RoleApiV2RetrieveRequest;

  try {
    const data = await api.roleApiV2Retrieve(body);
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

[**Role**](Role.md)

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

## roleApiV2Update

> RoleCreateUpdate roleApiV2Update(id, roleCreateUpdate)

### Example

```ts
import {
  Configuration,
  RoleApi,
} from '';
import type { RoleApiV2UpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new RoleApi(config);

  const body = {
    // number
    id: 56,
    // RoleCreateUpdate
    roleCreateUpdate: ...,
  } satisfies RoleApiV2UpdateRequest;

  try {
    const data = await api.roleApiV2Update(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                 | Type                                    | Description | Notes                     |
| -------------------- | --------------------------------------- | ----------- | ------------------------- |
| **id**               | `number`                                |             | [Defaults to `undefined`] |
| **roleCreateUpdate** | [RoleCreateUpdate](RoleCreateUpdate.md) |             |                           |

### Return type

[**RoleCreateUpdate**](RoleCreateUpdate.md)

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
