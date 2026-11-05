# ACLRole

## Properties

| Name                | Type   |
| ------------------- | ------ |
| `id`                | number |
| `name`              | string |
| `description`       | string |
| `currentPermission` | number |

## Example

```typescript
import type { ACLRole } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  description: null,
  currentPermission: null,
} satisfies ACLRole;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ACLRole;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
