# EntityImportExport

## Properties

| Name              | Type   |
| ----------------- | ------ |
| `id`              | number |
| `name`            | string |
| `note`            | string |
| `itemNamePattern` | string |
| `status`          | number |
| `createdUser`     | string |

## Example

```typescript
import type { EntityImportExport } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  note: null,
  itemNamePattern: null,
  status: null,
  createdUser: null,
} satisfies EntityImportExport;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityImportExport;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
