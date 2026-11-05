# EntryApi

All URIs are relative to _http://localhost_

| Method                                                                                                   | HTTP request                                          | Description |
| -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ----------- |
| [**entryApiV2AdvancedSearchChainCreate**](EntryApi.md#entryapiv2advancedsearchchaincreate)               | **POST** /entry/api/v2/advanced_search_chain/         |             |
| [**entryApiV2AdvancedSearchCreate**](EntryApi.md#entryapiv2advancedsearchcreate)                         | **POST** /entry/api/v2/advanced_search/               |             |
| [**entryApiV2AdvancedSearchResultExportCreate**](EntryApi.md#entryapiv2advancedsearchresultexportcreate) | **POST** /entry/api/v2/advanced_search_result_export/ |             |
| [**entryApiV2AliasBulkCreate**](EntryApi.md#entryapiv2aliasbulkcreate)                                   | **POST** /entry/api/v2/alias/bulk/                    |             |
| [**entryApiV2AliasCreate**](EntryApi.md#entryapiv2aliascreate)                                           | **POST** /entry/api/v2/alias/                         |             |
| [**entryApiV2AliasDestroy**](EntryApi.md#entryapiv2aliasdestroy)                                         | **DELETE** /entry/api/v2/alias/{id}                   |             |
| [**entryApiV2AliasList**](EntryApi.md#entryapiv2aliaslist)                                               | **GET** /entry/api/v2/{id}/alias/                     |             |
| [**entryApiV2AttrReferralsList**](EntryApi.md#entryapiv2attrreferralslist)                               | **GET** /entry/api/v2/{attr_id}/attr_referrals/       |             |
| [**entryApiV2AttrvRestorePartialUpdate**](EntryApi.md#entryapiv2attrvrestorepartialupdate)               | **PATCH** /entry/api/v2/{id}/attrv_restore/           |             |
| [**entryApiV2AttrvRestoreUpdate**](EntryApi.md#entryapiv2attrvrestoreupdate)                             | **PUT** /entry/api/v2/{id}/attrv_restore/             |             |
| [**entryApiV2BulkDeleteDestroy**](EntryApi.md#entryapiv2bulkdeletedestroy)                               | **DELETE** /entry/api/v2/bulk_delete/                 |             |
| [**entryApiV2BulkPartialUpdate**](EntryApi.md#entryapiv2bulkpartialupdate)                               | **PATCH** /entry/api/v2/bulk/                         |             |
| [**entryApiV2BulkUpdate**](EntryApi.md#entryapiv2bulkupdate)                                             | **PUT** /entry/api/v2/bulk/                           |             |
| [**entryApiV2CopyCreate**](EntryApi.md#entryapiv2copycreate)                                             | **POST** /entry/api/v2/{id}/copy/                     |             |
| [**entryApiV2Destroy**](EntryApi.md#entryapiv2destroy)                                                   | **DELETE** /entry/api/v2/{id}/                        |             |
| [**entryApiV2ExportCreate**](EntryApi.md#entryapiv2exportcreate)                                         | **POST** /entry/api/v2/{entity_id}/export/            |             |
| [**entryApiV2HistoriesList**](EntryApi.md#entryapiv2historieslist)                                       | **GET** /entry/api/v2/{id}/histories/                 |             |
| [**entryApiV2ImportCreate**](EntryApi.md#entryapiv2importcreate)                                         | **POST** /entry/api/v2/import/                        |             |
| [**entryApiV2ImportPreviewCreate**](EntryApi.md#entryapiv2importpreviewcreate)                           | **POST** /entry/api/v2/import/preview/                |             |
| [**entryApiV2ReferralList**](EntryApi.md#entryapiv2referrallist)                                         | **GET** /entry/api/v2/{id}/referral/                  |             |
| [**entryApiV2RestoreCreate**](EntryApi.md#entryapiv2restorecreate)                                       | **POST** /entry/api/v2/{id}/restore/                  |             |
| [**entryApiV2RestoreSelfHistoryCreate**](EntryApi.md#entryapiv2restoreselfhistorycreate)                 | **POST** /entry/api/v2/{id}/restore_self_history/     |             |
| [**entryApiV2Retrieve**](EntryApi.md#entryapiv2retrieve)                                                 | **GET** /entry/api/v2/{id}/                           |             |
| [**entryApiV2RollbackCreate**](EntryApi.md#entryapiv2rollbackcreate)                                     | **POST** /entry/api/v2/rollback/                      |             |
| [**entryApiV2SearchAttributeMatchesList**](EntryApi.md#entryapiv2searchattributematcheslist)             | **GET** /entry/api/v2/search/attribute_matches/       |             |
| [**entryApiV2SearchList**](EntryApi.md#entryapiv2searchlist)                                             | **GET** /entry/api/v2/search/                         |             |
| [**entryApiV2SelfHistoriesList**](EntryApi.md#entryapiv2selfhistorieslist)                               | **GET** /entry/api/v2/{id}/self_histories/            |             |
| [**entryApiV2Update**](EntryApi.md#entryapiv2update)                                                     | **PUT** /entry/api/v2/{id}/                           |             |

## entryApiV2AdvancedSearchChainCreate

> Array&lt;EntryBase&gt; entryApiV2AdvancedSearchChainCreate(entrySearchChain)

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2AdvancedSearchChainCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // EntrySearchChain
    entrySearchChain: ...,
  } satisfies EntryApiV2AdvancedSearchChainCreateRequest;

  try {
    const data = await api.entryApiV2AdvancedSearchChainCreate(body);
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
| **entrySearchChain** | [EntrySearchChain](EntrySearchChain.md) |             |       |

### Return type

[**Array&lt;EntryBase&gt;**](EntryBase.md)

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

## entryApiV2AdvancedSearchCreate

> AdvancedSearchResult entryApiV2AdvancedSearchCreate(advancedSearch)

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2AdvancedSearchCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // AdvancedSearch
    advancedSearch: ...,
  } satisfies EntryApiV2AdvancedSearchCreateRequest;

  try {
    const data = await api.entryApiV2AdvancedSearchCreate(body);
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
| **advancedSearch** | [AdvancedSearch](AdvancedSearch.md) |             |       |

### Return type

[**AdvancedSearchResult**](AdvancedSearchResult.md)

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

## entryApiV2AdvancedSearchResultExportCreate

> AdvancedSearchResultExport entryApiV2AdvancedSearchResultExportCreate(advancedSearchResultExport)

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2AdvancedSearchResultExportCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // AdvancedSearchResultExport
    advancedSearchResultExport: ...,
  } satisfies EntryApiV2AdvancedSearchResultExportCreateRequest;

  try {
    const data = await api.entryApiV2AdvancedSearchResultExportCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                           | Type                                                        | Description | Notes |
| ------------------------------ | ----------------------------------------------------------- | ----------- | ----- |
| **advancedSearchResultExport** | [AdvancedSearchResultExport](AdvancedSearchResultExport.md) |             |       |

### Return type

[**AdvancedSearchResultExport**](AdvancedSearchResultExport.md)

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

## entryApiV2AliasBulkCreate

> EntryAlias entryApiV2AliasBulkCreate(entryAlias)

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2AliasBulkCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // EntryAlias
    entryAlias: ...,
  } satisfies EntryApiV2AliasBulkCreateRequest;

  try {
    const data = await api.entryApiV2AliasBulkCreate(body);
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
| **entryAlias** | [EntryAlias](EntryAlias.md) |             |       |

### Return type

[**EntryAlias**](EntryAlias.md)

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

## entryApiV2AliasCreate

> EntryAlias entryApiV2AliasCreate(entryAlias)

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2AliasCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // EntryAlias
    entryAlias: ...,
  } satisfies EntryApiV2AliasCreateRequest;

  try {
    const data = await api.entryApiV2AliasCreate(body);
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
| **entryAlias** | [EntryAlias](EntryAlias.md) |             |       |

### Return type

[**EntryAlias**](EntryAlias.md)

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

## entryApiV2AliasDestroy

> entryApiV2AliasDestroy(id)

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2AliasDestroyRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
  } satisfies EntryApiV2AliasDestroyRequest;

  try {
    const data = await api.entryApiV2AliasDestroy(body);
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

## entryApiV2AliasList

> PaginatedEntryAliasList entryApiV2AliasList(id, limit, offset)

Entry API ViewSet with plugin override support. Plugin overrides are automatically handled by PluginOverrideMixin. Configure overrides via BACKEND_PLUGIN_ENTITY_OVERRIDES environment variable.

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2AliasListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
    // number | Number of results to return per page. (optional)
    limit: 56,
    // number | The initial index from which to return the results. (optional)
    offset: 56,
  } satisfies EntryApiV2AliasListRequest;

  try {
    const data = await api.entryApiV2AliasList(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name       | Type     | Description                                         | Notes                                |
| ---------- | -------- | --------------------------------------------------- | ------------------------------------ |
| **id**     | `number` |                                                     | [Defaults to `undefined`]            |
| **limit**  | `number` | Number of results to return per page.               | [Optional] [Defaults to `undefined`] |
| **offset** | `number` | The initial index from which to return the results. | [Optional] [Defaults to `undefined`] |

### Return type

[**PaginatedEntryAliasList**](PaginatedEntryAliasList.md)

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

## entryApiV2AttrReferralsList

> GetEntryAttrReferralList entryApiV2AttrReferralsList(attrId, keyword)

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2AttrReferralsListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    attrId: 56,
    // string (optional)
    keyword: keyword_example,
  } satisfies EntryApiV2AttrReferralsListRequest;

  try {
    const data = await api.entryApiV2AttrReferralsList(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name        | Type     | Description | Notes                                |
| ----------- | -------- | ----------- | ------------------------------------ |
| **attrId**  | `number` |             | [Defaults to `undefined`]            |
| **keyword** | `string` |             | [Optional] [Defaults to `undefined`] |

### Return type

[**GetEntryAttrReferralList**](GetEntryAttrReferralList.md)

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

## entryApiV2AttrvRestorePartialUpdate

> entryApiV2AttrvRestorePartialUpdate(id)

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2AttrvRestorePartialUpdateRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
  } satisfies EntryApiV2AttrvRestorePartialUpdateRequest;

  try {
    const data = await api.entryApiV2AttrvRestorePartialUpdate(body);
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
| **200**     | No response body | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## entryApiV2AttrvRestoreUpdate

> entryApiV2AttrvRestoreUpdate(id)

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2AttrvRestoreUpdateRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
  } satisfies EntryApiV2AttrvRestoreUpdateRequest;

  try {
    const data = await api.entryApiV2AttrvRestoreUpdate(body);
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
| **200**     | No response body | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## entryApiV2BulkDeleteDestroy

> entryApiV2BulkDeleteDestroy(attrinfo, ids, isAll)

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2BulkDeleteDestroyRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // string (optional)
    attrinfo: attrinfo_example,
    // Array<number> (optional)
    ids: ...,
    // boolean (optional)
    isAll: true,
  } satisfies EntryApiV2BulkDeleteDestroyRequest;

  try {
    const data = await api.entryApiV2BulkDeleteDestroy(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name         | Type            | Description | Notes                                |
| ------------ | --------------- | ----------- | ------------------------------------ |
| **attrinfo** | `string`        |             | [Optional] [Defaults to `undefined`] |
| **ids**      | `Array<number>` |             | [Optional]                           |
| **isAll**    | `boolean`       |             | [Optional] [Defaults to `undefined`] |

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

## entryApiV2BulkPartialUpdate

> EntryBulkUpdate entryApiV2BulkPartialUpdate(patchedEntryBulkUpdate)

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2BulkPartialUpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // PatchedEntryBulkUpdate (optional)
    patchedEntryBulkUpdate: ...,
  } satisfies EntryApiV2BulkPartialUpdateRequest;

  try {
    const data = await api.entryApiV2BulkPartialUpdate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                       | Type                                                | Description | Notes      |
| -------------------------- | --------------------------------------------------- | ----------- | ---------- |
| **patchedEntryBulkUpdate** | [PatchedEntryBulkUpdate](PatchedEntryBulkUpdate.md) |             | [Optional] |

### Return type

[**EntryBulkUpdate**](EntryBulkUpdate.md)

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

## entryApiV2BulkUpdate

> EntryBulkUpdate entryApiV2BulkUpdate(entryBulkUpdate)

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2BulkUpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // EntryBulkUpdate
    entryBulkUpdate: ...,
  } satisfies EntryApiV2BulkUpdateRequest;

  try {
    const data = await api.entryApiV2BulkUpdate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                | Type                                  | Description | Notes |
| ------------------- | ------------------------------------- | ----------- | ----- |
| **entryBulkUpdate** | [EntryBulkUpdate](EntryBulkUpdate.md) |             |       |

### Return type

[**EntryBulkUpdate**](EntryBulkUpdate.md)

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

## entryApiV2CopyCreate

> EntryCopy entryApiV2CopyCreate(id, entryCopy)

Entry API ViewSet with plugin override support. Plugin overrides are automatically handled by PluginOverrideMixin. Configure overrides via BACKEND_PLUGIN_ENTITY_OVERRIDES environment variable.

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2CopyCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
    // EntryCopy
    entryCopy: ...,
  } satisfies EntryApiV2CopyCreateRequest;

  try {
    const data = await api.entryApiV2CopyCreate(body);
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
| **entryCopy** | [EntryCopy](EntryCopy.md) |             |                           |

### Return type

[**EntryCopy**](EntryCopy.md)

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

## entryApiV2Destroy

> entryApiV2Destroy(id)

Entry API ViewSet with plugin override support. Plugin overrides are automatically handled by PluginOverrideMixin. Configure overrides via BACKEND_PLUGIN_ENTITY_OVERRIDES environment variable.

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2DestroyRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
  } satisfies EntryApiV2DestroyRequest;

  try {
    const data = await api.entryApiV2Destroy(body);
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

## entryApiV2ExportCreate

> EntryExport entryApiV2ExportCreate(entityId, entryExport)

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2ExportCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    entityId: 56,
    // EntryExport (optional)
    entryExport: ...,
  } satisfies EntryApiV2ExportCreateRequest;

  try {
    const data = await api.entryApiV2ExportCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name            | Type                          | Description | Notes                     |
| --------------- | ----------------------------- | ----------- | ------------------------- |
| **entityId**    | `number`                      |             | [Defaults to `undefined`] |
| **entryExport** | [EntryExport](EntryExport.md) |             | [Optional]                |

### Return type

[**EntryExport**](EntryExport.md)

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

## entryApiV2HistoriesList

> PaginatedEntryHistoryAttributeValueList entryApiV2HistoriesList(id, limit, offset)

Entry API ViewSet with plugin override support. Plugin overrides are automatically handled by PluginOverrideMixin. Configure overrides via BACKEND_PLUGIN_ENTITY_OVERRIDES environment variable.

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2HistoriesListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
    // number | Number of results to return per page. (optional)
    limit: 56,
    // number | The initial index from which to return the results. (optional)
    offset: 56,
  } satisfies EntryApiV2HistoriesListRequest;

  try {
    const data = await api.entryApiV2HistoriesList(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name       | Type     | Description                                         | Notes                                |
| ---------- | -------- | --------------------------------------------------- | ------------------------------------ |
| **id**     | `number` |                                                     | [Defaults to `undefined`]            |
| **limit**  | `number` | Number of results to return per page.               | [Optional] [Defaults to `undefined`] |
| **offset** | `number` | The initial index from which to return the results. | [Optional] [Defaults to `undefined`] |

### Return type

[**PaginatedEntryHistoryAttributeValueList**](PaginatedEntryHistoryAttributeValueList.md)

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

## entryApiV2ImportCreate

> entryApiV2ImportCreate(entryImportEntity, force, previewJobId)

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2ImportCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // Array<EntryImportEntity>
    entryImportEntity: ...,
    // boolean (optional)
    force: true,
    // number | The preview this import was approved from. Items changed by someone else since then are left alone and reported. (optional)
    previewJobId: 56,
  } satisfies EntryApiV2ImportCreateRequest;

  try {
    const data = await api.entryApiV2ImportCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                  | Type                       | Description                                                                                                      | Notes                                |
| --------------------- | -------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| **entryImportEntity** | `Array<EntryImportEntity>` |                                                                                                                  |                                      |
| **force**             | `boolean`                  |                                                                                                                  | [Optional] [Defaults to `false`]     |
| **previewJobId**      | `number`                   | The preview this import was approved from. Items changed by someone else since then are left alone and reported. | [Optional] [Defaults to `undefined`] |

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

## entryApiV2ImportPreviewCreate

> ImportPreviewJobs entryApiV2ImportPreviewCreate(entryImportEntity)

Start a job that reports what an item import file would change. Nothing is written: applying an item import also reindexes Elasticsearch and queues webhook and trigger jobs, so the preview runs the import\&#39;s decisions (the same serializers, the same change detection) and stops before the write. One job is started per model in the file, mirroring the import itself. The preview is optional -- posting to &#x60;&#x60;EntryImportAPI&#x60;&#x60; imports straight away.

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2ImportPreviewCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // Array<EntryImportEntity>
    entryImportEntity: ...,
  } satisfies EntryApiV2ImportPreviewCreateRequest;

  try {
    const data = await api.entryApiV2ImportPreviewCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name                  | Type                       | Description | Notes |
| --------------------- | -------------------------- | ----------- | ----- |
| **entryImportEntity** | `Array<EntryImportEntity>` |             |       |

### Return type

[**ImportPreviewJobs**](ImportPreviewJobs.md)

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

## entryApiV2ReferralList

> PaginatedEntryBaseList entryApiV2ReferralList(id, keyword, limit, offset)

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2ReferralListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
    // string (optional)
    keyword: keyword_example,
    // number | Number of results to return per page. (optional)
    limit: 56,
    // number | The initial index from which to return the results. (optional)
    offset: 56,
  } satisfies EntryApiV2ReferralListRequest;

  try {
    const data = await api.entryApiV2ReferralList(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name        | Type     | Description                                         | Notes                                |
| ----------- | -------- | --------------------------------------------------- | ------------------------------------ |
| **id**      | `number` |                                                     | [Defaults to `undefined`]            |
| **keyword** | `string` |                                                     | [Optional] [Defaults to `undefined`] |
| **limit**   | `number` | Number of results to return per page.               | [Optional] [Defaults to `undefined`] |
| **offset**  | `number` | The initial index from which to return the results. | [Optional] [Defaults to `undefined`] |

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

## entryApiV2RestoreCreate

> entryApiV2RestoreCreate(id)

Entry API ViewSet with plugin override support. Plugin overrides are automatically handled by PluginOverrideMixin. Configure overrides via BACKEND_PLUGIN_ENTITY_OVERRIDES environment variable.

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2RestoreCreateRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
  } satisfies EntryApiV2RestoreCreateRequest;

  try {
    const data = await api.entryApiV2RestoreCreate(body);
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
| **201**     | No response body | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

## entryApiV2RestoreSelfHistoryCreate

> EntrySelfHistoryRestore entryApiV2RestoreSelfHistoryCreate(id, entrySelfHistoryRestore)

Restore entry to a previous state from history

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2RestoreSelfHistoryCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
    // EntrySelfHistoryRestore
    entrySelfHistoryRestore: ...,
  } satisfies EntryApiV2RestoreSelfHistoryCreateRequest;

  try {
    const data = await api.entryApiV2RestoreSelfHistoryCreate(body);
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
| **entrySelfHistoryRestore** | [EntrySelfHistoryRestore](EntrySelfHistoryRestore.md) |             |                           |

### Return type

[**EntrySelfHistoryRestore**](EntrySelfHistoryRestore.md)

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

## entryApiV2Retrieve

> EntryRetrieve entryApiV2Retrieve(id)

Entry API ViewSet with plugin override support. Plugin overrides are automatically handled by PluginOverrideMixin. Configure overrides via BACKEND_PLUGIN_ENTITY_OVERRIDES environment variable.

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2RetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
  } satisfies EntryApiV2RetrieveRequest;

  try {
    const data = await api.entryApiV2Retrieve(body);
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

[**EntryRetrieve**](EntryRetrieve.md)

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

## entryApiV2RollbackCreate

> ItemRollback entryApiV2RollbackCreate(itemRollback)

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2RollbackCreateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // ItemRollback
    itemRollback: ...,
  } satisfies EntryApiV2RollbackCreateRequest;

  try {
    const data = await api.entryApiV2RollbackCreate(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name             | Type                            | Description | Notes |
| ---------------- | ------------------------------- | ----------- | ----- |
| **itemRollback** | [ItemRollback](ItemRollback.md) |             |       |

### Return type

[**ItemRollback**](ItemRollback.md)

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

## entryApiV2SearchAttributeMatchesList

> EntryNetworkSearchResponse entryApiV2SearchAttributeMatchesList(query, limit, offset)

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2SearchAttributeMatchesListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // string
    query: query_example,
    // number (optional)
    limit: 56,
    // number (optional)
    offset: 56,
  } satisfies EntryApiV2SearchAttributeMatchesListRequest;

  try {
    const data = await api.entryApiV2SearchAttributeMatchesList(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name       | Type     | Description | Notes                                |
| ---------- | -------- | ----------- | ------------------------------------ |
| **query**  | `string` |             | [Defaults to `undefined`]            |
| **limit**  | `number` |             | [Optional] [Defaults to `undefined`] |
| **offset** | `number` |             | [Optional] [Defaults to `undefined`] |

### Return type

[**EntryNetworkSearchResponse**](EntryNetworkSearchResponse.md)

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

## entryApiV2SearchList

> Array&lt;EntrySearch&gt; entryApiV2SearchList(limit, offset, query)

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2SearchListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number (optional)
    limit: 56,
    // number (optional)
    offset: 56,
    // string (optional)
    query: query_example,
  } satisfies EntryApiV2SearchListRequest;

  try {
    const data = await api.entryApiV2SearchList(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name       | Type     | Description | Notes                                |
| ---------- | -------- | ----------- | ------------------------------------ |
| **limit**  | `number` |             | [Optional] [Defaults to `undefined`] |
| **offset** | `number` |             | [Optional] [Defaults to `undefined`] |
| **query**  | `string` |             | [Optional] [Defaults to `undefined`] |

### Return type

[**Array&lt;EntrySearch&gt;**](EntrySearch.md)

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

## entryApiV2SelfHistoriesList

> PaginatedEntrySelfHistoryList entryApiV2SelfHistoriesList(id, limit, offset)

List entry self history records

### Example

```ts
import { Configuration, EntryApi } from "";
import type { EntryApiV2SelfHistoriesListRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
    // number | Number of results to return per page. (optional)
    limit: 56,
    // number | The initial index from which to return the results. (optional)
    offset: 56,
  } satisfies EntryApiV2SelfHistoriesListRequest;

  try {
    const data = await api.entryApiV2SelfHistoriesList(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name       | Type     | Description                                         | Notes                                |
| ---------- | -------- | --------------------------------------------------- | ------------------------------------ |
| **id**     | `number` |                                                     | [Defaults to `undefined`]            |
| **limit**  | `number` | Number of results to return per page.               | [Optional] [Defaults to `undefined`] |
| **offset** | `number` | The initial index from which to return the results. | [Optional] [Defaults to `undefined`] |

### Return type

[**PaginatedEntrySelfHistoryList**](PaginatedEntrySelfHistoryList.md)

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

## entryApiV2Update

> entryApiV2Update(id, entryUpdate)

Entry API ViewSet with plugin override support. Plugin overrides are automatically handled by PluginOverrideMixin. Configure overrides via BACKEND_PLUGIN_ENTITY_OVERRIDES environment variable.

### Example

```ts
import {
  Configuration,
  EntryApi,
} from '';
import type { EntryApiV2UpdateRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new EntryApi(config);

  const body = {
    // number
    id: 56,
    // EntryUpdate (optional)
    entryUpdate: ...,
  } satisfies EntryApiV2UpdateRequest;

  try {
    const data = await api.entryApiV2Update(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name            | Type                          | Description | Notes                     |
| --------------- | ----------------------------- | ----------- | ------------------------- |
| **id**          | `number`                      |             | [Defaults to `undefined`] |
| **entryUpdate** | [EntryUpdate](EntryUpdate.md) |             | [Optional]                |

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
