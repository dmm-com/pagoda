# PatchedEntryBulkUpdate

## Properties

| Name           | Type                                                                         |
| -------------- | ---------------------------------------------------------------------------- |
| `modelid`      | number                                                                       |
| `entryIds`     | Array&lt;number&gt;                                                          |
| `value`        | [AttributeData](AttributeData.md)                                            |
| `attrinfo`     | [Array&lt;AdvancedSearchResultAttrInfo&gt;](AdvancedSearchResultAttrInfo.md) |
| `referralName` | string                                                                       |
| `hintEntry`    | [EntryHint](EntryHint.md)                                                    |

## Example

```typescript
import type { PatchedEntryBulkUpdate } from "";

// TODO: Update the object below with actual values
const example = {
  modelid: null,
  entryIds: null,
  value: null,
  attrinfo: null,
  referralName: null,
  hintEntry: null,
} satisfies PatchedEntryBulkUpdate;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PatchedEntryBulkUpdate;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
