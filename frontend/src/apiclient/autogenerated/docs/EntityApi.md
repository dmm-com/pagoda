# EntityApi

All URIs are relative to _http://localhost_

| Method                                                                            | HTTP request                                  | Description |
| --------------------------------------------------------------------------------- | --------------------------------------------- | ----------- |
| [**entityApiV2AttrsList**](EntityApi.md#entityapiv2attrslist)                     | **GET** /entity/api/v2/attrs                  |             |
| [**entityApiV2Create**](EntityApi.md#entityapiv2create)                           | **POST** /entity/api/v2/                      |             |
| [**entityApiV2Destroy**](EntityApi.md#entityapiv2destroy)                         | **DELETE** /entity/api/v2/{id}/               |             |
| [**entityApiV2DiffRetrieve**](EntityApi.md#entityapiv2diffretrieve)               | **GET** /entity/api/v2/diff                   |             |
| [**entityApiV2EntriesCreate**](EntityApi.md#entityapiv2entriescreate)             | **POST** /entity/api/v2/{entity_id}/entries/  |             |
| [**entityApiV2EntriesList**](EntityApi.md#entityapiv2entrieslist)                 | **GET** /entity/api/v2/{entity_id}/entries/   |             |
| [**entityApiV2ExportCreate**](EntityApi.md#entityapiv2exportcreate)               | **POST** /entity/api/v2/export                |             |
| [**entityApiV2ExportCreate2**](EntityApi.md#entityapiv2exportcreate2)             | **POST** /entity/api/v2/{entity_id}/export    |             |
| [**entityApiV2HistoriesList**](EntityApi.md#entityapiv2historieslist)             | **GET** /entity/api/v2/{entity_id}/histories/ |             |
| [**entityApiV2ImportCreate**](EntityApi.md#entityapiv2importcreate)               | **POST** /entity/api/v2/import                |             |
| [**entityApiV2ImportPreviewCreate**](EntityApi.md#entityapiv2importpreviewcreate) | **POST** /entity/api/v2/import/preview        |             |
| [**entityApiV2List**](EntityApi.md#entityapiv2list)                               | **GET** /entity/api/v2/                       |             |
| [**entityApiV2Retrieve**](EntityApi.md#entityapiv2retrieve)                       | **GET** /entity/api/v2/{id}/                  |             |
| [**entityApiV2Update**](EntityApi.md#entityapiv2update)                           | **PUT** /entity/api/v2/{id}/                  |             |

## entityApiV2AttrsList

> Array&lt;EntityAttrIDandName&gt; entityApiV2AttrsList(entityIds, referralAttr)

### Example

```ts
import { Configuration, EntityApi } from "";
import type { EntityApiV2AttrsListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // string (optional)
    entityIds: entityIds_example,
    // string (optional)
    referralAttr: referralAttr_example,
  } satisfies EntityApiV2AttrsListRequest;

  try {
    const data = await api.entityApiV2AttrsList(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name             | Type     | Description | Notes                                |
| ---------------- | -------- | ----------- | ------------------------------------ |
| **entityIds**    | `string` |             | [Optional] [Defaults to `undefined`] |
| **referralAttr** | `string` |             | [Optional] [Defaults to `undefined`] |

### Return type

[**Array&lt;EntityAttrIDandName&gt;**](EntityAttrIDandName.md)

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

## entityApiV2Create

> entityApiV2Create(entityCreate, isToplevel)

### Example

```ts
import {
  Configuration,
  EntityApi,
} from '';
import type { EntityApiV2CreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // EntityCreate
    entityCreate: ...,
    // boolean (optional)
    isToplevel: true,
  } satisfies EntityApiV2CreateRequest;

  try {
    const data = await api.entityApiV2Create(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name             | Type                            | Description | Notes                                |
| ---------------- | ------------------------------- | ----------- | ------------------------------------ |
| **entityCreate** | [EntityCreate](EntityCreate.md) |             |                                      |
| **isToplevel**   | `boolean`                       |             | [Optional] [Defaults to `undefined`] |

### Return type

`void` (Empty response body)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: Not defined

### HTTP response details

| Status code | Description      | Response headers |
| ----------- | ---------------- | ---------------- |
| **202**     | No response body | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## entityApiV2Destroy

> entityApiV2Destroy(id, isToplevel)

### Example

```ts
import { Configuration, EntityApi } from "";
import type { EntityApiV2DestroyRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // number
    id: 56,
    // boolean (optional)
    isToplevel: true,
  } satisfies EntityApiV2DestroyRequest;

  try {
    const data = await api.entityApiV2Destroy(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name           | Type      | Description | Notes                                |
| -------------- | --------- | ----------- | ------------------------------------ |
| **id**         | `number`  |             | [Defaults to `undefined`]            |
| **isToplevel** | `boolean` |             | [Optional] [Defaults to `undefined`] |

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

## entityApiV2DiffRetrieve

> EntityDiff entityApiV2DiffRetrieve(attr, model, t0, t1)

Report entries whose attribute value differs between two points in time.

### Example

```ts
import {
  Configuration,
  EntityApi,
} from '';
import type { EntityApiV2DiffRetrieveRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // Array<string> | Name of the attribute to compare. Specify multiple times to compare several
    attr: ...,
    // string | Name of the Entity (model) to compare
    model: model_example,
    // Date | Earlier point in time
    t0: 2013-10-20T19:20:30+01:00,
    // Date | Later point in time
    t1: 2013-10-20T19:20:30+01:00,
  } satisfies EntityApiV2DiffRetrieveRequest;

  try {
    const data = await api.entityApiV2DiffRetrieve(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name      | Type            | Description                                                                 | Notes                     |
| --------- | --------------- | --------------------------------------------------------------------------- | ------------------------- |
| **attr**  | `Array<string>` | Name of the attribute to compare. Specify multiple times to compare several |                           |
| **model** | `string`        | Name of the Entity (model) to compare                                       | [Defaults to `undefined`] |
| **t0**    | `Date`          | Earlier point in time                                                       | [Defaults to `undefined`] |
| **t1**    | `Date`          | Later point in time                                                         | [Defaults to `undefined`] |

### Return type

[**EntityDiff**](EntityDiff.md)

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

## entityApiV2EntriesCreate

> entityApiV2EntriesCreate(entityId, entryCreate, withAlias)

Handle create action with plugin override support.

### Example

```ts
import {
  Configuration,
  EntityApi,
} from '';
import type { EntityApiV2EntriesCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // number
    entityId: 56,
    // EntryCreate
    entryCreate: ...,
    // string (optional)
    withAlias: withAlias_example,
  } satisfies EntityApiV2EntriesCreateRequest;

  try {
    const data = await api.entityApiV2EntriesCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name            | Type                          | Description | Notes                                |
| --------------- | ----------------------------- | ----------- | ------------------------------------ |
| **entityId**    | `number`                      |             | [Defaults to `undefined`]            |
| **entryCreate** | [EntryCreate](EntryCreate.md) |             |                                      |
| **withAlias**   | `string`                      |             | [Optional] [Defaults to `undefined`] |

### Return type

`void` (Empty response body)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: Not defined

### HTTP response details

| Status code | Description      | Response headers |
| ----------- | ---------------- | ---------------- |
| **202**     | No response body | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## entityApiV2EntriesList

> PaginatedEntryBaseList entityApiV2EntriesList(entityId, isActive, ordering, page, search, withAlias)

Handle list action with plugin override support.

### Example

```ts
import { Configuration, EntityApi } from "";
import type { EntityApiV2EntriesListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // number
    entityId: 56,
    // boolean (optional)
    isActive: true,
    // string | Which field to use when ordering the results. (optional)
    ordering: ordering_example,
    // number | A page number within the paginated result set. (optional)
    page: 56,
    // string | A search term. (optional)
    search: search_example,
    // string (optional)
    withAlias: withAlias_example,
  } satisfies EntityApiV2EntriesListRequest;

  try {
    const data = await api.entityApiV2EntriesList(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name          | Type      | Description                                    | Notes                                |
| ------------- | --------- | ---------------------------------------------- | ------------------------------------ |
| **entityId**  | `number`  |                                                | [Defaults to `undefined`]            |
| **isActive**  | `boolean` |                                                | [Optional] [Defaults to `undefined`] |
| **ordering**  | `string`  | Which field to use when ordering the results.  | [Optional] [Defaults to `undefined`] |
| **page**      | `number`  | A page number within the paginated result set. | [Optional] [Defaults to `undefined`] |
| **search**    | `string`  | A search term.                                 | [Optional] [Defaults to `undefined`] |
| **withAlias** | `string`  |                                                | [Optional] [Defaults to `undefined`] |

### Return type

[**PaginatedEntryBaseList**](PaginatedEntryBaseList.md)

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

## entityApiV2ExportCreate

> JobSerializers entityApiV2ExportCreate()

### Example

```ts
import { Configuration, EntityApi } from "";
import type { EntityApiV2ExportCreateRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  try {
    const data = await api.entityApiV2ExportCreate();
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

## entityApiV2ExportCreate2

> JobSerializers entityApiV2ExportCreate2(entityId)

### Example

```ts
import { Configuration, EntityApi } from "";
import type { EntityApiV2ExportCreate2Request } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // number
    entityId: 56,
  } satisfies EntityApiV2ExportCreate2Request;

  try {
    const data = await api.entityApiV2ExportCreate2(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name         | Type     | Description | Notes                     |
| ------------ | -------- | ----------- | ------------------------- |
| **entityId** | `number` |             | [Defaults to `undefined`] |

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

## entityApiV2HistoriesList

> PaginatedEntityHistoryList entityApiV2HistoriesList(entityId, limit, offset)

### Example

```ts
import { Configuration, EntityApi } from "";
import type { EntityApiV2HistoriesListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // number
    entityId: 56,
    // number | Number of results to return per page. (optional)
    limit: 56,
    // number | The initial index from which to return the results. (optional)
    offset: 56,
  } satisfies EntityApiV2HistoriesListRequest;

  try {
    const data = await api.entityApiV2HistoriesList(body);
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
| **entityId** | `number` |                                                     | [Defaults to `undefined`]            |
| **limit**    | `number` | Number of results to return per page.               | [Optional] [Defaults to `undefined`] |
| **offset**   | `number` | The initial index from which to return the results. | [Optional] [Defaults to `undefined`] |

### Return type

[**PaginatedEntityHistoryList**](PaginatedEntityHistoryList.md)

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

## entityApiV2ImportCreate

> entityApiV2ImportCreate(entityImportExportRoot)

### Example

```ts
import {
  Configuration,
  EntityApi,
} from '';
import type { EntityApiV2ImportCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // EntityImportExportRoot
    entityImportExportRoot: ...,
  } satisfies EntityApiV2ImportCreateRequest;

  try {
    const data = await api.entityApiV2ImportCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                       | Type                                                | Description | Notes |
| -------------------------- | --------------------------------------------------- | ----------- | ----- |
| **entityImportExportRoot** | [EntityImportExportRoot](EntityImportExportRoot.md) |             |       |

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

## entityApiV2ImportPreviewCreate

> ImportPreviewJob entityApiV2ImportPreviewCreate(entityImportExportRoot)

Start a job that reports what an import file would change. Previewing walks the same rows the import walks, so it costs the same: it is handed to a worker and this endpoint returns the job to poll, rather than holding a request open for as long as the import would take. That also means a preview has no row limit -- a file too big to preview in a request is exactly the file whose preview is worth waiting for. The preview stays optional: clients may post straight to &#x60;&#x60;EntityImportAPI&#x60;&#x60;.

### Example

```ts
import {
  Configuration,
  EntityApi,
} from '';
import type { EntityApiV2ImportPreviewCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // EntityImportExportRoot
    entityImportExportRoot: ...,
  } satisfies EntityApiV2ImportPreviewCreateRequest;

  try {
    const data = await api.entityApiV2ImportPreviewCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                       | Type                                                | Description | Notes |
| -------------------------- | --------------------------------------------------- | ----------- | ----- |
| **entityImportExportRoot** | [EntityImportExportRoot](EntityImportExportRoot.md) |             |       |

### Return type

[**ImportPreviewJob**](ImportPreviewJob.md)

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

## entityApiV2List

> PaginatedEntityListList entityApiV2List(isToplevel, limit, offset, ordering, search)

### Example

```ts
import { Configuration, EntityApi } from "";
import type { EntityApiV2ListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // boolean (optional)
    isToplevel: true,
    // number | Number of results to return per page. (optional)
    limit: 56,
    // number | The initial index from which to return the results. (optional)
    offset: 56,
    // string | Which field to use when ordering the results. (optional)
    ordering: ordering_example,
    // string | A search term. (optional)
    search: search_example,
  } satisfies EntityApiV2ListRequest;

  try {
    const data = await api.entityApiV2List(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name           | Type      | Description                                         | Notes                                |
| -------------- | --------- | --------------------------------------------------- | ------------------------------------ |
| **isToplevel** | `boolean` |                                                     | [Optional] [Defaults to `undefined`] |
| **limit**      | `number`  | Number of results to return per page.               | [Optional] [Defaults to `undefined`] |
| **offset**     | `number`  | The initial index from which to return the results. | [Optional] [Defaults to `undefined`] |
| **ordering**   | `string`  | Which field to use when ordering the results.       | [Optional] [Defaults to `undefined`] |
| **search**     | `string`  | A search term.                                      | [Optional] [Defaults to `undefined`] |

### Return type

[**PaginatedEntityListList**](PaginatedEntityListList.md)

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

## entityApiV2Retrieve

> EntityDetail entityApiV2Retrieve(id, isToplevel)

### Example

```ts
import { Configuration, EntityApi } from "";
import type { EntityApiV2RetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // number
    id: 56,
    // boolean (optional)
    isToplevel: true,
  } satisfies EntityApiV2RetrieveRequest;

  try {
    const data = await api.entityApiV2Retrieve(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name           | Type      | Description | Notes                                |
| -------------- | --------- | ----------- | ------------------------------------ |
| **id**         | `number`  |             | [Defaults to `undefined`]            |
| **isToplevel** | `boolean` |             | [Optional] [Defaults to `undefined`] |

### Return type

[**EntityDetail**](EntityDetail.md)

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

## entityApiV2Update

> entityApiV2Update(id, isToplevel, entityUpdate)

### Example

```ts
import {
  Configuration,
  EntityApi,
} from '';
import type { EntityApiV2UpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntityApi(config);

  const body = {
    // number
    id: 56,
    // boolean (optional)
    isToplevel: true,
    // EntityUpdate (optional)
    entityUpdate: ...,
  } satisfies EntityApiV2UpdateRequest;

  try {
    const data = await api.entityApiV2Update(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name             | Type                            | Description | Notes                                |
| ---------------- | ------------------------------- | ----------- | ------------------------------------ |
| **id**           | `number`                        |             | [Defaults to `undefined`]            |
| **isToplevel**   | `boolean`                       |             | [Optional] [Defaults to `undefined`] |
| **entityUpdate** | [EntityUpdate](EntityUpdate.md) |             | [Optional]                           |

### Return type

`void` (Empty response body)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`
- **Accept**: Not defined

### HTTP response details

| Status code | Description      | Response headers |
| ----------- | ---------------- | ---------------- |
| **202**     | No response body | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
