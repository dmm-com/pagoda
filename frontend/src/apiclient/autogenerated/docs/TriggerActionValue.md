# TriggerActionValue

## Properties

| Name       | Type                                                      |
| ---------- | --------------------------------------------------------- |
| `id`       | number                                                    |
| `strCond`  | string                                                    |
| `refCond`  | [TriggerActionValueRefCond](TriggerActionValueRefCond.md) |
| `boolCond` | boolean                                                   |

## Example

```typescript
import type { TriggerActionValue } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  strCond: null,
  refCond: null,
  boolCond: null,
} satisfies TriggerActionValue;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as TriggerActionValue;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
