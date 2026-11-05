# RolePermission

## Properties

| Name         | Type   |
| ------------ | ------ |
| `type`       | string |
| `id`         | number |
| `modelName`  | string |
| `name`       | string |
| `permission` | string |

## Example

```typescript
import type { RolePermission } from "";

// TODO: Update the object below with actual values
const example = {
  type: null,
  id: null,
  modelName: null,
  name: null,
  permission: null,
} satisfies RolePermission;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as RolePermission;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
