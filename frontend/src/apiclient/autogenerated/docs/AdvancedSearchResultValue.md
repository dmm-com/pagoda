# AdvancedSearchResultValue

## Properties

| Name          | Type                                                                                    |
| ------------- | --------------------------------------------------------------------------------------- |
| `attrs`       | [{ [key: string]: AdvancedSearchResultValueAttr; }](AdvancedSearchResultValueAttr.md)   |
| `joinedAttrs` | [{ [key: string]: AdvancedSearchResultJoinedAttr; }](AdvancedSearchResultJoinedAttr.md) |
| `entry`       | [AdvancedSearchResultValueEntry](AdvancedSearchResultValueEntry.md)                     |
| `entity`      | [AdvancedSearchResultValueEntity](AdvancedSearchResultValueEntity.md)                   |
| `referrals`   | [Array&lt;AdvancedSearchResultValueReferral&gt;](AdvancedSearchResultValueReferral.md)  |
| `isReadable`  | boolean                                                                                 |

## Example

```typescript
import type { AdvancedSearchResultValue } from "";

// TODO: Update the object below with actual values
const example = {
  attrs: null,
  joinedAttrs: null,
  entry: null,
  entity: null,
  referrals: null,
  isReadable: null,
} satisfies AdvancedSearchResultValue;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as AdvancedSearchResultValue;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
