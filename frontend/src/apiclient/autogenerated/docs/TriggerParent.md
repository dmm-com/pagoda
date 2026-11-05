# TriggerParent

## Properties

| Name         | Type                                                 |
| ------------ | ---------------------------------------------------- |
| `id`         | number                                               |
| `entity`     | [Entity](Entity.md)                                  |
| `actions`    | [Array&lt;TriggerAction&gt;](TriggerAction.md)       |
| `conditions` | [Array&lt;TriggerCondition&gt;](TriggerCondition.md) |

## Example

```typescript
import type { TriggerParent } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  entity: null,
  actions: null,
  conditions: null,
} satisfies TriggerParent;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as TriggerParent;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
