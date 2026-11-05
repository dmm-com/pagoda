# CommonApi

All URIs are relative to _http://localhost_

| Method                                                                            | HTTP request                           | Description |
| --------------------------------------------------------------------------------- | -------------------------------------- | ----------- |
| [**commonApiV2ImportCreate**](CommonApi.md#commonapiv2importcreate)               | **POST** /common/api/v2/import         |             |
| [**commonApiV2ImportPreviewCreate**](CommonApi.md#commonapiv2importpreviewcreate) | **POST** /common/api/v2/import/preview |             |

## commonApiV2ImportCreate

> CommonImportJob commonApiV2ImportCreate(force, previewJobId, requestBody)

Import any kind of model, item, user, group or role file through a single endpoint. The kind of the file (model, item, user, group or role) is detected from its content. A file that matches none of them is rejected with 400 before any job is created. Applying the file always runs as a job.

### Example

```ts
import { Configuration, CommonApi } from "";
import type { CommonApiV2ImportCreateRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new CommonApi(config);

  const body = {
    // boolean (optional)
    force: true,
    // number | The preview an item import was approved from. (optional)
    previewJobId: 56,
    // { [key: string]: any; } (optional)
    requestBody: Object,
  } satisfies CommonApiV2ImportCreateRequest;

  try {
    const data = await api.commonApiV2ImportCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name             | Type                      | Description                                   | Notes                                |
| ---------------- | ------------------------- | --------------------------------------------- | ------------------------------------ |
| **force**        | `boolean`                 |                                               | [Optional] [Defaults to `false`]     |
| **previewJobId** | `number`                  | The preview an item import was approved from. | [Optional] [Defaults to `undefined`] |
| **requestBody**  | `{ [key: string]: any; }` |                                               | [Optional]                           |

### Return type

[**CommonImportJob**](CommonImportJob.md)

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

## commonApiV2ImportPreviewCreate

> CommonImportJob commonApiV2ImportPreviewCreate(requestBody)

Start the preview job(s) of an entity or item import file. The file\&#39;s type is detected the same way as for the import. Users, groups and roles have no preview, so those files are rejected with 400 before any job is created. The response has the import\&#39;s shape, with the preview job ids in &#x60;&#x60;job_ids&#x60;&#x60;.

### Example

```ts
import { Configuration, CommonApi } from "";
import type { CommonApiV2ImportPreviewCreateRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new CommonApi(config);

  const body = {
    // { [key: string]: any; } (optional)
    requestBody: Object,
  } satisfies CommonApiV2ImportPreviewCreateRequest;

  try {
    const data = await api.commonApiV2ImportPreviewCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name            | Type                      | Description | Notes      |
| --------------- | ------------------------- | ----------- | ---------- |
| **requestBody** | `{ [key: string]: any; }` |             | [Optional] |

### Return type

[**CommonImportJob**](CommonImportJob.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/yaml`
- **Accept**: `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **202**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
