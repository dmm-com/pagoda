# PasswordResetConfirm

## Properties

| Name        | Type   |
| ----------- | ------ |
| `uidb64`    | string |
| `token`     | string |
| `password1` | string |
| `password2` | string |

## Example

```typescript
import type { PasswordResetConfirm } from "";

// TODO: Update the object below with actual values
const example = {
  uidb64: null,
  token: null,
  password1: null,
  password2: null,
} satisfies PasswordResetConfirm;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PasswordResetConfirm;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
