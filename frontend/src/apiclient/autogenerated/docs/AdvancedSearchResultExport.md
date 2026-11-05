# AdvancedSearchResultExport

## Properties

| Name               | Type                                                                         |
| ------------------ | ---------------------------------------------------------------------------- |
| `entities`         | Array&lt;number&gt;                                                          |
| `attrinfo`         | [Array&lt;AdvancedSearchResultAttrInfo&gt;](AdvancedSearchResultAttrInfo.md) |
| `joinAttrs`        | [Array&lt;AdvancedSearchJoinAttrInfo&gt;](AdvancedSearchJoinAttrInfo.md)     |
| `hasReferral`      | boolean                                                                      |
| `referralName`     | string                                                                       |
| `includeReferrals` | Array&lt;number&gt;                                                          |
| `excludeReferrals` | Array&lt;number&gt;                                                          |
| `isAllEntities`    | boolean                                                                      |
| `exportStyle`      | string                                                                       |
| `hintEntry`        | [EntryHint](EntryHint.md)                                                    |

## Example

```typescript
import type { AdvancedSearchResultExport } from "";

// TODO: Update the object below with actual values
const example = {
  entities: null,
  attrinfo: null,
  joinAttrs: null,
  hasReferral: null,
  referralName: null,
  includeReferrals: null,
  excludeReferrals: null,
  isAllEntities: null,
  exportStyle: null,
  hintEntry: null,
} satisfies AdvancedSearchResultExport;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as AdvancedSearchResultExport;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
