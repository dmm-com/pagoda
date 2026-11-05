# AclApi

All URIs are relative to _http://localhost_

| Method                                                           | HTTP request                          | Description |
| ---------------------------------------------------------------- | ------------------------------------- | ----------- |
| [**aclApiV2AclsHistoryList**](AclApi.md#aclapiv2aclshistorylist) | **GET** /acl/api/v2/acls/{id}/history |             |
| [**aclApiV2AclsRetrieve**](AclApi.md#aclapiv2aclsretrieve)       | **GET** /acl/api/v2/acls/{id}         |             |
| [**aclApiV2AclsUpdate**](AclApi.md#aclapiv2aclsupdate)           | **PUT** /acl/api/v2/acls/{id}         |             |

## aclApiV2AclsHistoryList

> Array&lt;ACLHistory&gt; aclApiV2AclsHistoryList(id)

ACL History API - Performance Optimization Strategy: This method implements significant query reduction optimizations: 1. select_related: Bulk fetch of related data (history_user, content_type) 2. Bulk fetch: ACLBase name information bulk retrieval and caching 3. prev_record cache: Pre-build history relationships to solve N+1 problem This minimizes DB access within serializers, reducing queries from 30+ to around 10.

### Example

```ts
import { Configuration, AclApi } from "";
import type { AclApiV2AclsHistoryListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new AclApi(config);

  const body = {
    // number
    id: 56,
  } satisfies AclApiV2AclsHistoryListRequest;

  try {
    const data = await api.aclApiV2AclsHistoryList(body);
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

[**Array&lt;ACLHistory&gt;**](ACLHistory.md)

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

## aclApiV2AclsRetrieve

> ACL aclApiV2AclsRetrieve(id)

### Example

```ts
import { Configuration, AclApi } from "";
import type { AclApiV2AclsRetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new AclApi(config);

  const body = {
    // number
    id: 56,
  } satisfies AclApiV2AclsRetrieveRequest;

  try {
    const data = await api.aclApiV2AclsRetrieve(body);
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

[**ACL**](ACL.md)

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

## aclApiV2AclsUpdate

> ACL aclApiV2AclsUpdate(id, aCL)

### Example

```ts
import {
  Configuration,
  AclApi,
} from '';
import type { AclApiV2AclsUpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new AclApi(config);

  const body = {
    // number
    id: 56,
    // ACL (optional)
    aCL: ...,
  } satisfies AclApiV2AclsUpdateRequest;

  try {
    const data = await api.aclApiV2AclsUpdate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name    | Type          | Description | Notes                     |
| ------- | ------------- | ----------- | ------------------------- |
| **id**  | `number`      |             | [Defaults to `undefined`] |
| **aCL** | [ACL](ACL.md) |             | [Optional]                |

### Return type

[**ACL**](ACL.md)

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
