# TriggerParentCreate

## Properties

| Name         | Type                                                             |
| ------------ | ---------------------------------------------------------------- |
| `id`         | number                                                           |
| `entityId`   | number                                                           |
| `conditions` | [Array&lt;TriggerConditionUpdate&gt;](TriggerConditionUpdate.md) |
| `actions`    | [Array&lt;TriggerActionUpdate&gt;](TriggerActionUpdate.md)       |

## Example

```typescript
import type { TriggerParentCreate } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  entityId: null,
  conditions: null,
  actions: null,
} satisfies TriggerParentCreate;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as TriggerParentCreate;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
