# IsolationParentCreateUpdate

## Properties

| Name         | Type                                                                             |
| ------------ | -------------------------------------------------------------------------------- |
| `id`         | number                                                                           |
| `isDeleted`  | boolean                                                                          |
| `conditions` | [Array&lt;IsolationConditionCreateUpdate&gt;](IsolationConditionCreateUpdate.md) |
| `action`     | [IsolationActionCreateUpdate](IsolationActionCreateUpdate.md)                    |

## Example

```typescript
import type { IsolationParentCreateUpdate } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  isDeleted: null,
  conditions: null,
  action: null,
} satisfies IsolationParentCreateUpdate;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as IsolationParentCreateUpdate;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
