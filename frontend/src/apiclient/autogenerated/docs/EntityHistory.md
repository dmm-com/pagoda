# EntityHistory

Extended serializer with simple-history changes for entity history.

## Properties

| Name        | Type                                                       |
| ----------- | ---------------------------------------------------------- |
| `operation` | number                                                     |
| `time`      | Date                                                       |
| `username`  | string                                                     |
| `text`      | string                                                     |
| `targetObj` | string                                                     |
| `isDetail`  | boolean                                                    |
| `changes`   | [Array&lt;EntityHistoryChange&gt;](EntityHistoryChange.md) |

## Example

```typescript
import type { EntityHistory } from "";

// TODO: Update the object below with actual values
const example = {
  operation: null,
  time: null,
  username: null,
  text: null,
  targetObj: null,
  isDetail: null,
  changes: null,
} satisfies EntityHistory;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityHistory;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
