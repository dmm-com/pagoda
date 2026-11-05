# AdvancedSearch

## Properties

| Name               | Type                                                                         |
| ------------------ | ---------------------------------------------------------------------------- |
| `entities`         | Array&lt;number&gt;                                                          |
| `attrinfo`         | [Array&lt;AdvancedSearchResultAttrInfo&gt;](AdvancedSearchResultAttrInfo.md) |
| `joinAttrs`        | [Array&lt;AdvancedSearchJoinAttrInfo&gt;](AdvancedSearchJoinAttrInfo.md)     |
| `hasReferral`      | boolean                                                                      |
| `referralName`     | string                                                                       |
| `isOutputAll`      | boolean                                                                      |
| `isAllEntities`    | boolean                                                                      |
| `entryLimit`       | number                                                                       |
| `entryOffset`      | number                                                                       |
| `hintEntry`        | [EntryHint](EntryHint.md)                                                    |
| `excludeReferrals` | Array&lt;number&gt;                                                          |
| `includeReferrals` | Array&lt;number&gt;                                                          |
| `sort`             | [AdvancedSearchSort](AdvancedSearchSort.md)                                  |

## Example

```typescript
import type { AdvancedSearch } from "";

// TODO: Update the object below with actual values
const example = {
  entities: null,
  attrinfo: null,
  joinAttrs: null,
  hasReferral: null,
  referralName: null,
  isOutputAll: null,
  isAllEntities: null,
  entryLimit: null,
  entryOffset: null,
  hintEntry: null,
  excludeReferrals: null,
  includeReferrals: null,
  sort: null,
} satisfies AdvancedSearch;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as AdvancedSearch;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
