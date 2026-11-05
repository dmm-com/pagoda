# RoleCreateUpdate

## Properties

| Name          | Type                |
| ------------- | ------------------- |
| `isActive`    | boolean             |
| `name`        | string              |
| `description` | string              |
| `users`       | Array&lt;number&gt; |
| `groups`      | Array&lt;number&gt; |
| `adminUsers`  | Array&lt;number&gt; |
| `adminGroups` | Array&lt;number&gt; |

## Example

```typescript
import type { RoleCreateUpdate } from "";

// TODO: Update the object below with actual values
const example = {
  isActive: null,
  name: null,
  description: null,
  users: null,
  groups: null,
  adminUsers: null,
  adminGroups: null,
} satisfies RoleCreateUpdate;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as RoleCreateUpdate;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
