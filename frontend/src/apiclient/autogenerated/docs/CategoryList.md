# CategoryList

## Properties

| Name         | Type                                             |
| ------------ | ------------------------------------------------ |
| `id`         | number                                           |
| `name`       | string                                           |
| `note`       | string                                           |
| `models`     | [Array&lt;CategoryEntity&gt;](CategoryEntity.md) |
| `priority`   | number                                           |
| `permission` | number                                           |

## Example

```typescript
import type { CategoryList } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  note: null,
  models: null,
  priority: null,
  permission: null,
} satisfies CategoryList;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as CategoryList;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
