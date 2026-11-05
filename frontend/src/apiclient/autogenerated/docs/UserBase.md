# UserBase

## Properties

| Name          | Type    |
| ------------- | ------- |
| `id`          | number  |
| `username`    | string  |
| `email`       | string  |
| `isSuperuser` | boolean |
| `dateJoined`  | string  |

## Example

```typescript
import type { UserBase } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  username: null,
  email: null,
  isSuperuser: null,
  dateJoined: null,
} satisfies UserBase;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as UserBase;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
