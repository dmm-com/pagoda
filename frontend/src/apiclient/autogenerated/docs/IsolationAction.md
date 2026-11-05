# IsolationAction

## Properties

| Name           | Type                                            |
| -------------- | ----------------------------------------------- |
| `id`           | number                                          |
| `preventFrom`  | [IsolationActionModel](IsolationActionModel.md) |
| `isPreventAll` | boolean                                         |

## Example

```typescript
import type { IsolationAction } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  preventFrom: null,
  isPreventAll: null,
} satisfies IsolationAction;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as IsolationAction;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
