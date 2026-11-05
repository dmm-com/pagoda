# UserPassword

## Properties

| Name        | Type   |
| ----------- | ------ |
| `oldPasswd` | string |
| `newPasswd` | string |
| `chkPasswd` | string |

## Example

```typescript
import type { UserPassword } from "";

// TODO: Update the object below with actual values
const example = {
  oldPasswd: null,
  newPasswd: null,
  chkPasswd: null,
} satisfies UserPassword;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as UserPassword;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
