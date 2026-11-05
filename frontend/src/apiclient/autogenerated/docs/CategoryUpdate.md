# CategoryUpdate

## Properties

| Name       | Type                                             |
| ---------- | ------------------------------------------------ |
| `name`     | string                                           |
| `note`     | string                                           |
| `models`   | [Array&lt;CategoryEntity&gt;](CategoryEntity.md) |
| `priority` | number                                           |

## Example

```typescript
import type { CategoryUpdate } from "";

// TODO: Update the object below with actual values
const example = {
  name: null,
  note: null,
  models: null,
  priority: null,
} satisfies CategoryUpdate;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as CategoryUpdate;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
