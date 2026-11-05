# TriggerCondition

## Properties

| Name        | Type                                                      |
| ----------- | --------------------------------------------------------- |
| `id`        | number                                                    |
| `attr`      | [EntityAttr](EntityAttr.md)                               |
| `strCond`   | string                                                    |
| `refCond`   | [TriggerActionValueRefCond](TriggerActionValueRefCond.md) |
| `boolCond`  | boolean                                                   |
| `isUnmatch` | boolean                                                   |

## Example

```typescript
import type { TriggerCondition } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  attr: null,
  strCond: null,
  refCond: null,
  boolCond: null,
  isUnmatch: null,
} satisfies TriggerCondition;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as TriggerCondition;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
