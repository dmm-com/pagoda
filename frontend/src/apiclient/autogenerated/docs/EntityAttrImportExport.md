# EntityAttrImportExport

## Properties

| Name          | Type    |
| ------------- | ------- |
| `id`          | number  |
| `name`        | string  |
| `type`        | number  |
| `entity`      | string  |
| `isMandatory` | boolean |
| `createdUser` | string  |
| `refer`       | string  |

## Example

```typescript
import type { EntityAttrImportExport } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  type: null,
  entity: null,
  isMandatory: null,
  createdUser: null,
  refer: null,
} satisfies EntityAttrImportExport;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityAttrImportExport;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
