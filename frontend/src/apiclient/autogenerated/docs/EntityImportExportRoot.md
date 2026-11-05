# EntityImportExportRoot

## Properties

| Name         | Type                                                             |
| ------------ | ---------------------------------------------------------------- |
| `entity`     | [Array&lt;EntityImportExport&gt;](EntityImportExport.md)         |
| `entityAttr` | [Array&lt;EntityAttrImportExport&gt;](EntityAttrImportExport.md) |

## Example

```typescript
import type { EntityImportExportRoot } from "";

// TODO: Update the object below with actual values
const example = {
  entity: null,
  entityAttr: null,
} satisfies EntityImportExportRoot;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityImportExportRoot;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
