# EntityList

## Properties

| Name              | Type    |
| ----------------- | ------- |
| `id`              | number  |
| `name`            | string  |
| `note`            | string  |
| `itemNamePattern` | string  |
| `itemNameType`    | string  |
| `status`          | number  |
| `isToplevel`      | boolean |
| `permission`      | number  |

## Example

```typescript
import type { EntityList } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  note: null,
  itemNamePattern: null,
  itemNameType: null,
  status: null,
  isToplevel: null,
  permission: null,
} satisfies EntityList;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityList;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
