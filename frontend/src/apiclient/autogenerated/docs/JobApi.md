# JobApi

All URIs are relative to _http://localhost_

| Method                                                                           | HTTP request                              | Description |
| -------------------------------------------------------------------------------- | ----------------------------------------- | ----------- |
| [**jobApiV2Destroy**](JobApi.md#jobapiv2destroy)                                 | **DELETE** /job/api/v2/{id}/              |             |
| [**jobApiV2DownloadRetrieve**](JobApi.md#jobapiv2downloadretrieve)               | **GET** /job/api/v2/{id}/download         |             |
| [**jobApiV2JobsList**](JobApi.md#jobapiv2jobslist)                               | **GET** /job/api/v2/jobs                  |             |
| [**jobApiV2PreviewDownloadRetrieve**](JobApi.md#jobapiv2previewdownloadretrieve) | **GET** /job/api/v2/{id}/preview/download |             |
| [**jobApiV2PreviewRetrieve**](JobApi.md#jobapiv2previewretrieve)                 | **GET** /job/api/v2/{id}/preview          |             |
| [**jobApiV2Retrieve**](JobApi.md#jobapiv2retrieve)                               | **GET** /job/api/v2/{id}/                 |             |

## jobApiV2Destroy

> jobApiV2Destroy(id)

### Example

```ts
import { Configuration, JobApi } from "";
import type { JobApiV2DestroyRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new JobApi(config);

  const body = {
    // number
    id: 56,
  } satisfies JobApiV2DestroyRequest;

  try {
    const data = await api.jobApiV2Destroy(body);
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

## jobApiV2DownloadRetrieve

> JobSerializers jobApiV2DownloadRetrieve(id, encode)

### Example

```ts
import { Configuration, JobApi } from "";
import type { JobApiV2DownloadRetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new JobApi(config);

  const body = {
    // number
    id: 56,
    // 'shift_jis' | 'utf-8' (optional)
    encode: encode_example,
  } satisfies JobApiV2DownloadRetrieveRequest;

  try {
    const data = await api.jobApiV2DownloadRetrieve(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name       | Type                 | Description | Notes                                                               |
| ---------- | -------------------- | ----------- | ------------------------------------------------------------------- |
| **id**     | `number`             |             | [Defaults to `undefined`]                                           |
| **encode** | `shift_jis`, `utf-8` |             | [Optional] [Defaults to `&#39;utf-8&#39;`] [Enum: shift_jis, utf-8] |

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
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## jobApiV2JobsList

> PaginatedJobSerializersList jobApiV2JobsList(allUsers, createdAfter, createdBefore, jobId, limit, offset, operation, status, targetId, text, user)

### Example

```ts
import {
  Configuration,
  JobApi,
} from '';
import type { JobApiV2JobsListRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new JobApi(config);

  const body = {
    // boolean | If true and the requester is a superuser, return jobs for all users. (optional)
    allUsers: true,
    // Date (optional)
    createdAfter: 2013-10-20T19:20:30+01:00,
    // Date (optional)
    createdBefore: 2013-10-20T19:20:30+01:00,
    // number (optional)
    jobId: 56,
    // number | Number of results to return per page. (optional)
    limit: 56,
    // number | The initial index from which to return the results. (optional)
    offset: 56,
    // string | One operation ID or comma-separated operation IDs. (optional)
    operation: operation_example,
    // number (optional)
    status: 56,
    // number (optional)
    targetId: 56,
    // string | Case-insensitive partial match on job message. (optional)
    text: text_example,
    // string | Case-insensitive partial match on username. (optional)
    user: user_example,
  } satisfies JobApiV2JobsListRequest;

  try {
    const data = await api.jobApiV2JobsList(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name              | Type      | Description                                                          | Notes                                |
| ----------------- | --------- | -------------------------------------------------------------------- | ------------------------------------ |
| **allUsers**      | `boolean` | If true and the requester is a superuser, return jobs for all users. | [Optional] [Defaults to `false`]     |
| **createdAfter**  | `Date`    |                                                                      | [Optional] [Defaults to `undefined`] |
| **createdBefore** | `Date`    |                                                                      | [Optional] [Defaults to `undefined`] |
| **jobId**         | `number`  |                                                                      | [Optional] [Defaults to `undefined`] |
| **limit**         | `number`  | Number of results to return per page.                                | [Optional] [Defaults to `undefined`] |
| **offset**        | `number`  | The initial index from which to return the results.                  | [Optional] [Defaults to `undefined`] |
| **operation**     | `string`  | One operation ID or comma-separated operation IDs.                   | [Optional] [Defaults to `undefined`] |
| **status**        | `number`  |                                                                      | [Optional] [Defaults to `undefined`] |
| **targetId**      | `number`  |                                                                      | [Optional] [Defaults to `undefined`] |
| **text**          | `string`  | Case-insensitive partial match on job message.                       | [Optional] [Defaults to `undefined`] |
| **user**          | `string`  | Case-insensitive partial match on username.                          | [Optional] [Defaults to `undefined`] |

### Return type

[**PaginatedJobSerializersList**](PaginatedJobSerializersList.md)

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

## jobApiV2PreviewDownloadRetrieve

> string jobApiV2PreviewDownloadRetrieve(id, encode)

Download a whole preview as CSV. A preview of a large file is worth reading carefully, and a browser table is not where that is done. This hands over every row that was kept, in the order the file listed them.

### Example

```ts
import { Configuration, JobApi } from "";
import type { JobApiV2PreviewDownloadRetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new JobApi(config);

  const body = {
    // number
    id: 56,
    // 'shift_jis' | 'utf-8' (optional)
    encode: encode_example,
  } satisfies JobApiV2PreviewDownloadRetrieveRequest;

  try {
    const data = await api.jobApiV2PreviewDownloadRetrieve(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name       | Type                 | Description | Notes                                                               |
| ---------- | -------------------- | ----------- | ------------------------------------------------------------------- |
| **id**     | `number`             |             | [Defaults to `undefined`]                                           |
| **encode** | `shift_jis`, `utf-8` |             | [Optional] [Defaults to `&#39;utf-8&#39;`] [Enum: shift_jis, utf-8] |

### Return type

**string**

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

## jobApiV2PreviewRetrieve

> ImportPreview jobApiV2PreviewRetrieve(id, action, limit, offset)

Return the result of a preview job, one page of rows at a time. The whole preview is kept as a single cached payload, so the rows are paged out from here rather than queried: a preview of a large file can run to thousands of rows, and no client wants them in one response. The rows a user came for -- the errors, the changes -- may sit anywhere in a long file, so they are filtered here rather than after paging.

### Example

```ts
import { Configuration, JobApi } from "";
import type { JobApiV2PreviewRetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new JobApi(config);

  const body = {
    // number
    id: 56,
    // string | Comma-separated actions to list, e.g. \'error,skip\'. Defaults to every action. The summary always covers them all. (optional)
    action: action_example,
    // number (optional)
    limit: 56,
    // number (optional)
    offset: 56,
  } satisfies JobApiV2PreviewRetrieveRequest;

  try {
    const data = await api.jobApiV2PreviewRetrieve(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name       | Type     | Description                                                                                                                 | Notes                                |
| ---------- | -------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| **id**     | `number` |                                                                                                                             | [Defaults to `undefined`]            |
| **action** | `string` | Comma-separated actions to list, e.g. \&#39;error,skip\&#39;. Defaults to every action. The summary always covers them all. | [Optional] [Defaults to `undefined`] |
| **limit**  | `number` |                                                                                                                             | [Optional] [Defaults to `100`]       |
| **offset** | `number` |                                                                                                                             | [Optional] [Defaults to `0`]         |

### Return type

[**ImportPreview**](ImportPreview.md)

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

## jobApiV2Retrieve

> JobSerializers jobApiV2Retrieve(id)

### Example

```ts
import { Configuration, JobApi } from "";
import type { JobApiV2RetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new JobApi(config);

  const body = {
    // number
    id: 56,
  } satisfies JobApiV2RetrieveRequest;

  try {
    const data = await api.jobApiV2Retrieve(body);
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

[**JobSerializers**](JobSerializers.md)

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
