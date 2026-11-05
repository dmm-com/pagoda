# GroupApi

All URIs are relative to _http://localhost_

| Method                                                                       | HTTP request                         | Description |
| ---------------------------------------------------------------------------- | ------------------------------------ | ----------- |
| [**groupApiV2GroupsCreate**](GroupApi.md#groupapiv2groupscreate)             | **POST** /group/api/v2/groups        |             |
| [**groupApiV2GroupsDestroy**](GroupApi.md#groupapiv2groupsdestroy)           | **DELETE** /group/api/v2/groups/{id} |             |
| [**groupApiV2GroupsExportCreate**](GroupApi.md#groupapiv2groupsexportcreate) | **POST** /group/api/v2/groups/export |             |
| [**groupApiV2GroupsImportCreate**](GroupApi.md#groupapiv2groupsimportcreate) | **POST** /group/api/v2/groups/import |             |
| [**groupApiV2GroupsList**](GroupApi.md#groupapiv2groupslist)                 | **GET** /group/api/v2/groups         |             |
| [**groupApiV2GroupsRetrieve**](GroupApi.md#groupapiv2groupsretrieve)         | **GET** /group/api/v2/groups/{id}    |             |
| [**groupApiV2GroupsTreeList**](GroupApi.md#groupapiv2groupstreelist)         | **GET** /group/api/v2/groups/tree    |             |
| [**groupApiV2GroupsUpdate**](GroupApi.md#groupapiv2groupsupdate)             | **PUT** /group/api/v2/groups/{id}    |             |

## groupApiV2GroupsCreate

> GroupCreateUpdate groupApiV2GroupsCreate(groupCreateUpdate)

### Example

```ts
import {
  Configuration,
  GroupApi,
} from '';
import type { GroupApiV2GroupsCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new GroupApi(config);

  const body = {
    // GroupCreateUpdate
    groupCreateUpdate: ...,
  } satisfies GroupApiV2GroupsCreateRequest;

  try {
    const data = await api.groupApiV2GroupsCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                  | Type                                      | Description | Notes |
| --------------------- | ----------------------------------------- | ----------- | ----- |
| **groupCreateUpdate** | [GroupCreateUpdate](GroupCreateUpdate.md) |             |       |

### Return type

[**GroupCreateUpdate**](GroupCreateUpdate.md)

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

## groupApiV2GroupsDestroy

> groupApiV2GroupsDestroy(id)

### Example

```ts
import { Configuration, GroupApi } from "";
import type { GroupApiV2GroupsDestroyRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new GroupApi(config);

  const body = {
    // number
    id: 56,
  } satisfies GroupApiV2GroupsDestroyRequest;

  try {
    const data = await api.groupApiV2GroupsDestroy(body);
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

## groupApiV2GroupsExportCreate

> JobSerializers groupApiV2GroupsExportCreate()

### Example

```ts
import { Configuration, GroupApi } from "";
import type { GroupApiV2GroupsExportCreateRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new GroupApi(config);

  try {
    const data = await api.groupApiV2GroupsExportCreate();
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

## groupApiV2GroupsImportCreate

> groupApiV2GroupsImportCreate(groupImport)

### Example

```ts
import {
  Configuration,
  GroupApi,
} from '';
import type { GroupApiV2GroupsImportCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new GroupApi(config);

  const body = {
    // GroupImport
    groupImport: ...,
  } satisfies GroupApiV2GroupsImportCreateRequest;

  try {
    const data = await api.groupApiV2GroupsImportCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name            | Type                          | Description | Notes |
| --------------- | ----------------------------- | ----------- | ----- |
| **groupImport** | [GroupImport](GroupImport.md) |             |       |

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

## groupApiV2GroupsList

> PaginatedGroupList groupApiV2GroupsList(ordering, page, search)

### Example

```ts
import { Configuration, GroupApi } from "";
import type { GroupApiV2GroupsListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new GroupApi(config);

  const body = {
    // string | Which field to use when ordering the results. (optional)
    ordering: ordering_example,
    // number | A page number within the paginated result set. (optional)
    page: 56,
    // string | A search term. (optional)
    search: search_example,
  } satisfies GroupApiV2GroupsListRequest;

  try {
    const data = await api.groupApiV2GroupsList(body);
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

[**PaginatedGroupList**](PaginatedGroupList.md)

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

## groupApiV2GroupsRetrieve

> Group groupApiV2GroupsRetrieve(id)

### Example

```ts
import { Configuration, GroupApi } from "";
import type { GroupApiV2GroupsRetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new GroupApi(config);

  const body = {
    // number
    id: 56,
  } satisfies GroupApiV2GroupsRetrieveRequest;

  try {
    const data = await api.groupApiV2GroupsRetrieve(body);
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

[**Group**](Group.md)

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

## groupApiV2GroupsTreeList

> Array&lt;GroupTreeV2&gt; groupApiV2GroupsTreeList(ordering, search)

### Example

```ts
import { Configuration, GroupApi } from "";
import type { GroupApiV2GroupsTreeListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new GroupApi(config);

  const body = {
    // string | Which field to use when ordering the results. (optional)
    ordering: ordering_example,
    // string | A search term. (optional)
    search: search_example,
  } satisfies GroupApiV2GroupsTreeListRequest;

  try {
    const data = await api.groupApiV2GroupsTreeList(body);
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

[**Array&lt;GroupTreeV2&gt;**](GroupTreeV2.md)

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

## groupApiV2GroupsUpdate

> GroupCreateUpdate groupApiV2GroupsUpdate(id, groupCreateUpdate)

### Example

```ts
import {
  Configuration,
  GroupApi,
} from '';
import type { GroupApiV2GroupsUpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new GroupApi(config);

  const body = {
    // number
    id: 56,
    // GroupCreateUpdate
    groupCreateUpdate: ...,
  } satisfies GroupApiV2GroupsUpdateRequest;

  try {
    const data = await api.groupApiV2GroupsUpdate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                  | Type                                      | Description | Notes                     |
| --------------------- | ----------------------------------------- | ----------- | ------------------------- |
| **id**                | `number`                                  |             | [Defaults to `undefined`] |
| **groupCreateUpdate** | [GroupCreateUpdate](GroupCreateUpdate.md) |             |                           |

### Return type

[**GroupCreateUpdate**](GroupCreateUpdate.md)

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
