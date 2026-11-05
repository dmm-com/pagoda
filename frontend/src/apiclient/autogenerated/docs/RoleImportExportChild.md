# RoleImportExportChild

## Properties

| Name          | Type                                 |
| ------------- | ------------------------------------ |
| `id`          | number                               |
| `name`        | string                               |
| `description` | string                               |
| `users`       | Array&lt;string&gt;                  |
| `groups`      | Array&lt;string&gt;                  |
| `adminUsers`  | Array&lt;string&gt;                  |
| `adminGroups` | Array&lt;string&gt;                  |
| `permissions` | Array&lt;{ [key: string]: any; }&gt; |

## Example

```typescript
import type { RoleImportExportChild } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  description: null,
  users: null,
  groups: null,
  adminUsers: null,
  adminGroups: null,
  permissions: null,
} satisfies RoleImportExportChild;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as RoleImportExportChild;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
