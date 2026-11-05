# JobTarget

## Properties

| Name         | Type   |
| ------------ | ------ |
| `id`         | number |
| `name`       | string |
| `schemaId`   | number |
| `schemaName` | string |

## Example

```typescript
import type { JobTarget } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  schemaId: null,
  schemaName: null,
} satisfies JobTarget;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as JobTarget;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
