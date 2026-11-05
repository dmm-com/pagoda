# EntryBase

## Properties

| Name          | Type                                     |
| ------------- | ---------------------------------------- |
| `id`          | number                                   |
| `name`        | string                                   |
| `schema`      | [Entity](Entity.md)                      |
| `isActive`    | boolean                                  |
| `deletedUser` | [UserBase](UserBase.md)                  |
| `deletedTime` | Date                                     |
| `updatedTime` | Date                                     |
| `aliases`     | [Array&lt;EntryAlias&gt;](EntryAlias.md) |
| `permission`  | number                                   |

## Example

```typescript
import type { EntryBase } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  schema: null,
  isActive: null,
  deletedUser: null,
  deletedTime: null,
  updatedTime: null,
  aliases: null,
  permission: null,
} satisfies EntryBase;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntryBase;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
