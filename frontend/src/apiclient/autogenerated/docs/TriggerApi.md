# TriggerApi

All URIs are relative to _http://localhost_

| Method                                                         | HTTP request                    | Description |
| -------------------------------------------------------------- | ------------------------------- | ----------- |
| [**triggerApiV2Create**](TriggerApi.md#triggerapiv2create)     | **POST** /trigger/api/v2/       |             |
| [**triggerApiV2Destroy**](TriggerApi.md#triggerapiv2destroy)   | **DELETE** /trigger/api/v2/{id} |             |
| [**triggerApiV2List**](TriggerApi.md#triggerapiv2list)         | **GET** /trigger/api/v2/        |             |
| [**triggerApiV2Retrieve**](TriggerApi.md#triggerapiv2retrieve) | **GET** /trigger/api/v2/{id}    |             |
| [**triggerApiV2Update**](TriggerApi.md#triggerapiv2update)     | **PUT** /trigger/api/v2/{id}    |             |

## triggerApiV2Create

> TriggerParentCreate triggerApiV2Create(triggerParentCreate)

### Example

```ts
import {
  Configuration,
  TriggerApi,
} from '';
import type { TriggerApiV2CreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new TriggerApi(config);

  const body = {
    // TriggerParentCreate (optional)
    triggerParentCreate: ...,
  } satisfies TriggerApiV2CreateRequest;

  try {
    const data = await api.triggerApiV2Create(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                    | Type                                          | Description | Notes      |
| ----------------------- | --------------------------------------------- | ----------- | ---------- |
| **triggerParentCreate** | [TriggerParentCreate](TriggerParentCreate.md) |             | [Optional] |

### Return type

[**TriggerParentCreate**](TriggerParentCreate.md)

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

## triggerApiV2Destroy

> triggerApiV2Destroy(id)

### Example

```ts
import { Configuration, TriggerApi } from "";
import type { TriggerApiV2DestroyRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new TriggerApi(config);

  const body = {
    // number
    id: 56,
  } satisfies TriggerApiV2DestroyRequest;

  try {
    const data = await api.triggerApiV2Destroy(body);
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

## triggerApiV2List

> PaginatedTriggerParentList triggerApiV2List(page)

### Example

```ts
import { Configuration, TriggerApi } from "";
import type { TriggerApiV2ListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new TriggerApi(config);

  const body = {
    // number | A page number within the paginated result set. (optional)
    page: 56,
  } satisfies TriggerApiV2ListRequest;

  try {
    const data = await api.triggerApiV2List(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name     | Type     | Description                                    | Notes                                |
| -------- | -------- | ---------------------------------------------- | ------------------------------------ |
| **page** | `number` | A page number within the paginated result set. | [Optional] [Defaults to `undefined`] |

### Return type

[**PaginatedTriggerParentList**](PaginatedTriggerParentList.md)

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

## triggerApiV2Retrieve

> TriggerParent triggerApiV2Retrieve(id)

### Example

```ts
import { Configuration, TriggerApi } from "";
import type { TriggerApiV2RetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new TriggerApi(config);

  const body = {
    // number
    id: 56,
  } satisfies TriggerApiV2RetrieveRequest;

  try {
    const data = await api.triggerApiV2Retrieve(body);
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

[**TriggerParent**](TriggerParent.md)

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

## triggerApiV2Update

> TriggerParentUpdate triggerApiV2Update(id, triggerParentUpdate)

### Example

```ts
import {
  Configuration,
  TriggerApi,
} from '';
import type { TriggerApiV2UpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new TriggerApi(config);

  const body = {
    // number
    id: 56,
    // TriggerParentUpdate (optional)
    triggerParentUpdate: ...,
  } satisfies TriggerApiV2UpdateRequest;

  try {
    const data = await api.triggerApiV2Update(body);
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
| **triggerParentUpdate** | [TriggerParentUpdate](TriggerParentUpdate.md) |             | [Optional]                |

### Return type

[**TriggerParentUpdate**](TriggerParentUpdate.md)

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
