# UserRetrieveToken

## Properties

| Name       | Type   |
| ---------- | ------ |
| `value`    | string |
| `lifetime` | number |
| `expire`   | string |
| `created`  | string |

## Example

```typescript
import type { UserRetrieveToken } from "";

// TODO: Update the object below with actual values
const example = {
  value: null,
  lifetime: null,
  expire: null,
  created: null,
} satisfies UserRetrieveToken;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as UserRetrieveToken;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
