# ACL

## Properties

| Name                | Type                                     |
| ------------------- | ---------------------------------------- |
| `id`                | number                                   |
| `name`              | string                                   |
| `isPublic`          | boolean                                  |
| `defaultPermission` | number                                   |
| `objtype`           | number                                   |
| `aclSettings`       | [Array&lt;ACLSetting&gt;](ACLSetting.md) |
| `roles`             | [Array&lt;ACLRole&gt;](ACLRole.md)       |
| `parent`            | [ACLParent](ACLParent.md)                |

## Example

```typescript
import type { ACL } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  isPublic: null,
  defaultPermission: null,
  objtype: null,
  aclSettings: null,
  roles: null,
  parent: null,
} satisfies ACL;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ACL;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
