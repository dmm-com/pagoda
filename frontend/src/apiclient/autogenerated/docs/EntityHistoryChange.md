# EntityHistoryChange

Serializer for individual change items in entity history.

## Properties

| Name     | Type   |
| -------- | ------ |
| `action` | string |
| `target` | string |
| `before` | any    |
| `after`  | any    |

## Example

```typescript
import type { EntityHistoryChange } from "";

// TODO: Update the object below with actual values
const example = {
  action: null,
  target: null,
  before: null,
  after: null,
} satisfies EntityHistoryChange;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityHistoryChange;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
