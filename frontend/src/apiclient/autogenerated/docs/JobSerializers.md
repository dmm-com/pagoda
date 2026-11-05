# JobSerializers

## Properties

| Name         | Type                      |
| ------------ | ------------------------- |
| `id`         | number                    |
| `user`       | string                    |
| `text`       | string                    |
| `status`     | number                    |
| `operation`  | number                    |
| `createdAt`  | Date                      |
| `target`     | [JobTarget](JobTarget.md) |
| `passedTime` | number                    |

## Example

```typescript
import type { JobSerializers } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  user: null,
  text: null,
  status: null,
  operation: null,
  createdAt: null,
  target: null,
  passedTime: null,
} satisfies JobSerializers;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as JobSerializers;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
