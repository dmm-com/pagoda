# UserRetrieve

## Properties

| Name               | Type                                      |
| ------------------ | ----------------------------------------- |
| `id`               | number                                    |
| `username`         | string                                    |
| `email`            | string                                    |
| `isSuperuser`      | boolean                                   |
| `dateJoined`       | string                                    |
| `token`            | [UserRetrieveToken](UserRetrieveToken.md) |
| `authenticateType` | number                                    |
| `parentUser`       | number                                    |
| `groups`           | [Array&lt;UserGroup&gt;](UserGroup.md)    |
| `roles`            | [Array&lt;UserRole&gt;](UserRole.md)      |
| `coUsers`          | Array&lt;{ [key: string]: any; }&gt;      |

## Example

```typescript
import type { UserRetrieve } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  username: null,
  email: null,
  isSuperuser: null,
  dateJoined: null,
  token: null,
  authenticateType: null,
  parentUser: null,
  groups: null,
  roles: null,
  coUsers: null,
} satisfies UserRetrieve;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as UserRetrieve;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
