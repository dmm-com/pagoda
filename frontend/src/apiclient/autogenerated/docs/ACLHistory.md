# ACLHistory

## Properties

| Name      | Type                                                 |
| --------- | ---------------------------------------------------- |
| `user`    | [ACLHistoryUser](ACLHistoryUser.md)                  |
| `time`    | Date                                                 |
| `name`    | string                                               |
| `changes` | [Array&lt;ACLHistoryChange&gt;](ACLHistoryChange.md) |

## Example

```typescript
import type { ACLHistory } from "";

// TODO: Update the object below with actual values
const example = {
  user: null,
  time: null,
  name: null,
  changes: null,
} satisfies ACLHistory;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ACLHistory;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
