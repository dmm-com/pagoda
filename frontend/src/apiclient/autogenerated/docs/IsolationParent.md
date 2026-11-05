# IsolationParent

## Properties

| Name         | Type                                                     |
| ------------ | -------------------------------------------------------- |
| `id`         | number                                                   |
| `conditions` | [Array&lt;IsolationCondition&gt;](IsolationCondition.md) |
| `action`     | [IsolationAction](IsolationAction.md)                    |

## Example

```typescript
import type { IsolationParent } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  conditions: null,
  action: null,
} satisfies IsolationParent;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as IsolationParent;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
