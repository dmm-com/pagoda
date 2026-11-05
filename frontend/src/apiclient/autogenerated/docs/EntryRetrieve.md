# EntryRetrieve

## Properties

| Name                | Type                                                     |
| ------------------- | -------------------------------------------------------- |
| `id`                | number                                                   |
| `name`              | string                                                   |
| `schema`            | [Entity](Entity.md)                                      |
| `isActive`          | boolean                                                  |
| `deletedUser`       | [UserBase](UserBase.md)                                  |
| `deletedTime`       | Date                                                     |
| `attrs`             | [Array&lt;EntryAttributeType&gt;](EntryAttributeType.md) |
| `isPublic`          | boolean                                                  |
| `permission`        | number                                                   |
| `hasOngoingChanges` | boolean                                                  |

## Example

```typescript
import type { EntryRetrieve } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  schema: null,
  isActive: null,
  deletedUser: null,
  deletedTime: null,
  attrs: null,
  isPublic: null,
  permission: null,
  hasOngoingChanges: null,
} satisfies EntryRetrieve;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntryRetrieve;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
