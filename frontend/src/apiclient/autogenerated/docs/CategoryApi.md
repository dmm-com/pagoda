# CategoryApi

All URIs are relative to _http://localhost_

| Method                                                            | HTTP request                      | Description |
| ----------------------------------------------------------------- | --------------------------------- | ----------- |
| [**categoryApiV2Create**](CategoryApi.md#categoryapiv2create)     | **POST** /category/api/v2/        |             |
| [**categoryApiV2Destroy**](CategoryApi.md#categoryapiv2destroy)   | **DELETE** /category/api/v2/{id}/ |             |
| [**categoryApiV2List**](CategoryApi.md#categoryapiv2list)         | **GET** /category/api/v2/         |             |
| [**categoryApiV2Retrieve**](CategoryApi.md#categoryapiv2retrieve) | **GET** /category/api/v2/{id}/    |             |
| [**categoryApiV2Update**](CategoryApi.md#categoryapiv2update)     | **PUT** /category/api/v2/{id}/    |             |

## categoryApiV2Create

> CategoryCreate categoryApiV2Create(categoryCreate)

### Example

```ts
import {
  Configuration,
  CategoryApi,
} from '';
import type { CategoryApiV2CreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new CategoryApi(config);

  const body = {
    // CategoryCreate
    categoryCreate: ...,
  } satisfies CategoryApiV2CreateRequest;

  try {
    const data = await api.categoryApiV2Create(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name               | Type                                | Description | Notes |
| ------------------ | ----------------------------------- | ----------- | ----- |
| **categoryCreate** | [CategoryCreate](CategoryCreate.md) |             |       |

### Return type

[**CategoryCreate**](CategoryCreate.md)

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

## categoryApiV2Destroy

> categoryApiV2Destroy(id)

### Example

```ts
import { Configuration, CategoryApi } from "";
import type { CategoryApiV2DestroyRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new CategoryApi(config);

  const body = {
    // number
    id: 56,
  } satisfies CategoryApiV2DestroyRequest;

  try {
    const data = await api.categoryApiV2Destroy(body);
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

## categoryApiV2List

> PaginatedCategoryListList categoryApiV2List(limit, offset, ordering, search)

### Example

```ts
import { Configuration, CategoryApi } from "";
import type { CategoryApiV2ListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new CategoryApi(config);

  const body = {
    // number | Number of results to return per page. (optional)
    limit: 56,
    // number | The initial index from which to return the results. (optional)
    offset: 56,
    // string | Which field to use when ordering the results. (optional)
    ordering: ordering_example,
    // string | A search term. (optional)
    search: search_example,
  } satisfies CategoryApiV2ListRequest;

  try {
    const data = await api.categoryApiV2List(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name         | Type     | Description                                         | Notes                                |
| ------------ | -------- | --------------------------------------------------- | ------------------------------------ |
| **limit**    | `number` | Number of results to return per page.               | [Optional] [Defaults to `undefined`] |
| **offset**   | `number` | The initial index from which to return the results. | [Optional] [Defaults to `undefined`] |
| **ordering** | `string` | Which field to use when ordering the results.       | [Optional] [Defaults to `undefined`] |
| **search**   | `string` | A search term.                                      | [Optional] [Defaults to `undefined`] |

### Return type

[**PaginatedCategoryListList**](PaginatedCategoryListList.md)

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

## categoryApiV2Retrieve

> CategoryList categoryApiV2Retrieve(id)

### Example

```ts
import { Configuration, CategoryApi } from "";
import type { CategoryApiV2RetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new CategoryApi(config);

  const body = {
    // number
    id: 56,
  } satisfies CategoryApiV2RetrieveRequest;

  try {
    const data = await api.categoryApiV2Retrieve(body);
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

[**CategoryList**](CategoryList.md)

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

## categoryApiV2Update

> CategoryUpdate categoryApiV2Update(id, categoryUpdate)

### Example

```ts
import {
  Configuration,
  CategoryApi,
} from '';
import type { CategoryApiV2UpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new CategoryApi(config);

  const body = {
    // number
    id: 56,
    // CategoryUpdate
    categoryUpdate: ...,
  } satisfies CategoryApiV2UpdateRequest;

  try {
    const data = await api.categoryApiV2Update(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name               | Type                                | Description | Notes                     |
| ------------------ | ----------------------------------- | ----------- | ------------------------- |
| **id**             | `number`                            |             | [Defaults to `undefined`] |
| **categoryUpdate** | [CategoryUpdate](CategoryUpdate.md) |             |                           |

### Return type

[**CategoryUpdate**](CategoryUpdate.md)

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
