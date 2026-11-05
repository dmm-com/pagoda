# IsolationConditionCreateUpdate

## Properties

| Name        | Type    |
| ----------- | ------- |
| `attrId`    | number  |
| `strCond`   | string  |
| `refCondId` | number  |
| `boolCond`  | boolean |
| `isUnmatch` | boolean |

## Example

```typescript
import type { IsolationConditionCreateUpdate } from "";

// TODO: Update the object below with actual values
const example = {
  attrId: null,
  strCond: null,
  refCondId: null,
  boolCond: null,
  isUnmatch: null,
} satisfies IsolationConditionCreateUpdate;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as IsolationConditionCreateUpdate;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
