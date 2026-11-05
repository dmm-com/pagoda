# Role

## Properties

| Name          | Type                                             |
| ------------- | ------------------------------------------------ |
| `id`          | number                                           |
| `isActive`    | boolean                                          |
| `name`        | string                                           |
| `description` | string                                           |
| `users`       | [Array&lt;RoleUser&gt;](RoleUser.md)             |
| `groups`      | [Array&lt;RoleGroup&gt;](RoleGroup.md)           |
| `adminUsers`  | [Array&lt;RoleUser&gt;](RoleUser.md)             |
| `adminGroups` | [Array&lt;RoleGroup&gt;](RoleGroup.md)           |
| `isEditable`  | boolean                                          |
| `permissions` | [Array&lt;RolePermission&gt;](RolePermission.md) |

## Example

```typescript
import type { Role } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  isActive: null,
  name: null,
  description: null,
  users: null,
  groups: null,
  adminUsers: null,
  adminGroups: null,
  isEditable: null,
  permissions: null,
} satisfies Role;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as Role;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
