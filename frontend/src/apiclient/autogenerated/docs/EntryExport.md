# EntryExport

## Properties

| Name        | Type                                                                     |
| ----------- | ------------------------------------------------------------------------ |
| `format`    | string                                                                   |
| `joinAttrs` | [Array&lt;AdvancedSearchJoinAttrInfo&gt;](AdvancedSearchJoinAttrInfo.md) |

## Example

```typescript
import type { EntryExport } from "";

// TODO: Update the object below with actual values
const example = {
  format: null,
  joinAttrs: null,
} satisfies EntryExport;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntryExport;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
