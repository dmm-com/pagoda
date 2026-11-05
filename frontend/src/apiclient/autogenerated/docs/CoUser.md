# CoUser

## Properties

| Name       | Type   |
| ---------- | ------ |
| `userId`   | number |
| `username` | string |
| `email`    | string |

## Example

```typescript
import type { CoUser } from "";

// TODO: Update the object below with actual values
const example = {
  userId: null,
  username: null,
  email: null,
} satisfies CoUser;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as CoUser;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
