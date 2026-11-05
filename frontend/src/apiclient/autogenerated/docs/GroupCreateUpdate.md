# GroupCreateUpdate

## Properties

| Name          | Type                |
| ------------- | ------------------- |
| `id`          | number              |
| `name`        | string              |
| `displayName` | string              |
| `parentGroup` | number              |
| `members`     | Array&lt;number&gt; |

## Example

```typescript
import type { GroupCreateUpdate } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  displayName: null,
  parentGroup: null,
  members: null,
} satisfies GroupCreateUpdate;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as GroupCreateUpdate;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
