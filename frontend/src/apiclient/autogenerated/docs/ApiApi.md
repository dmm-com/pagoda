# ApiApi

All URIs are relative to _http://localhost_

| Method                                               | HTTP request         | Description |
| ---------------------------------------------------- | -------------------- | ----------- |
| [**apiSchemaRetrieve**](ApiApi.md#apischemaretrieve) | **GET** /api/schema/ |             |

## apiSchemaRetrieve

> { [key: string]: any; } apiSchemaRetrieve(format, lang)

OpenApi3 schema for this API. Format can be selected via content negotiation. - YAML: application/vnd.oai.openapi - JSON: application/vnd.oai.openapi+json

### Example

```ts
import { Configuration, ApiApi } from "";
import type { ApiSchemaRetrieveRequest } from "";

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({
    // To configure API key authorization: cookieAuth
    apiKey: "YOUR API KEY",
    // To configure API key authorization: tokenAuth
    apiKey: "YOUR API KEY",
  });
  const api = new ApiApi(config);

  const body = {
    // 'json' | 'yaml' (optional)
    format: format_example,
    // 'af' | 'ar' | 'ar-dz' | 'ast' | 'az' | 'be' | 'bg' | 'bn' | 'br' | 'bs' | 'ca' | 'ckb' | 'cs' | 'cy' | 'da' | 'de' | 'dsb' | 'el' | 'en' | 'en-au' | 'en-gb' | 'eo' | 'es' | 'es-ar' | 'es-co' | 'es-mx' | 'es-ni' | 'es-ve' | 'et' | 'eu' | 'fa' | 'fi' | 'fr' | 'fy' | 'ga' | 'gd' | 'gl' | 'he' | 'hi' | 'hr' | 'hsb' | 'hu' | 'hy' | 'ia' | 'id' | 'ig' | 'io' | 'is' | 'it' | 'ja' | 'ka' | 'kab' | 'kk' | 'km' | 'kn' | 'ko' | 'ky' | 'lb' | 'lt' | 'lv' | 'mk' | 'ml' | 'mn' | 'mr' | 'ms' | 'my' | 'nb' | 'ne' | 'nl' | 'nn' | 'os' | 'pa' | 'pl' | 'pt' | 'pt-br' | 'ro' | 'ru' | 'sk' | 'sl' | 'sq' | 'sr' | 'sr-latn' | 'sv' | 'sw' | 'ta' | 'te' | 'tg' | 'th' | 'tk' | 'tr' | 'tt' | 'udm' | 'ug' | 'uk' | 'ur' | 'uz' | 'vi' | 'zh-hans' | 'zh-hant' (optional)
    lang: lang_example,
  } satisfies ApiSchemaRetrieveRequest;

  try {
    const data = await api.apiSchemaRetrieve(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

| Name       | Type                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Description | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **format** | `json`, `yaml`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |             | [Optional] [Defaults to `undefined`] [Enum: json, yaml]                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **lang**   | `af`, `ar`, `ar-dz`, `ast`, `az`, `be`, `bg`, `bn`, `br`, `bs`, `ca`, `ckb`, `cs`, `cy`, `da`, `de`, `dsb`, `el`, `en`, `en-au`, `en-gb`, `eo`, `es`, `es-ar`, `es-co`, `es-mx`, `es-ni`, `es-ve`, `et`, `eu`, `fa`, `fi`, `fr`, `fy`, `ga`, `gd`, `gl`, `he`, `hi`, `hr`, `hsb`, `hu`, `hy`, `ia`, `id`, `ig`, `io`, `is`, `it`, `ja`, `ka`, `kab`, `kk`, `km`, `kn`, `ko`, `ky`, `lb`, `lt`, `lv`, `mk`, `ml`, `mn`, `mr`, `ms`, `my`, `nb`, `ne`, `nl`, `nn`, `os`, `pa`, `pl`, `pt`, `pt-br`, `ro`, `ru`, `sk`, `sl`, `sq`, `sr`, `sr-latn`, `sv`, `sw`, `ta`, `te`, `tg`, `th`, `tk`, `tr`, `tt`, `udm`, `ug`, `uk`, `ur`, `uz`, `vi`, `zh-hans`, `zh-hant` |             | [Optional] [Defaults to `undefined`] [Enum: af, ar, ar-dz, ast, az, be, bg, bn, br, bs, ca, ckb, cs, cy, da, de, dsb, el, en, en-au, en-gb, eo, es, es-ar, es-co, es-mx, es-ni, es-ve, et, eu, fa, fi, fr, fy, ga, gd, gl, he, hi, hr, hsb, hu, hy, ia, id, ig, io, is, it, ja, ka, kab, kk, km, kn, ko, ky, lb, lt, lv, mk, ml, mn, mr, ms, my, nb, ne, nl, nn, os, pa, pl, pt, pt-br, ro, ru, sk, sl, sq, sr, sr-latn, sv, sw, ta, te, tg, th, tk, tr, tt, udm, ug, uk, ur, uz, vi, zh-hans, zh-hant] |

### Return type

**{ [key: string]: any; }**

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/vnd.oai.openapi`, `application/yaml`, `application/vnd.oai.openapi+json`, `application/json`

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     |             | -                |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
