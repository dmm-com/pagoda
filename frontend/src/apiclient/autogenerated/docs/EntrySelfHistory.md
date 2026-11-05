# EntrySelfHistory

Serializer for Entry self history records using simple_history

## Properties

| Name          | Type   |
| ------------- | ------ |
| `historyId`   | number |
| `name`        | string |
| `prevName`    | string |
| `historyDate` | Date   |
| `historyUser` | string |
| `historyType` | string |

## Example

```typescript
import type { EntrySelfHistory } from "";

// TODO: Update the object below with actual values
const example = {
  historyId: null,
  name: null,
  prevName: null,
  historyDate: null,
  historyUser: null,
  historyType: null,
} satisfies EntrySelfHistory;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntrySelfHistory;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
