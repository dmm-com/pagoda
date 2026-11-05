# TriggerAction

## Properties

| Name     | Type                                                     |
| -------- | -------------------------------------------------------- |
| `id`     | number                                                   |
| `attr`   | [EntityAttr](EntityAttr.md)                              |
| `values` | [Array&lt;TriggerActionValue&gt;](TriggerActionValue.md) |

## Example

```typescript
import type { TriggerAction } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  attr: null,
  values: null,
} satisfies TriggerAction;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as TriggerAction;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
