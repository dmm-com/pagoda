# CommonImportJob

## Properties

| Name     | Type                |
| -------- | ------------------- |
| `type`   | string              |
| `jobIds` | Array&lt;number&gt; |
| `error`  | Array&lt;string&gt; |

## Example

```typescript
import type { CommonImportJob } from "";

// TODO: Update the object below with actual values
const example = {
  type: null,
  jobIds: null,
  error: null,
} satisfies CommonImportJob;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as CommonImportJob;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
