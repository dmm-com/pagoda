# ImportPreviewJobsResult

## Properties

| Name    | Type                                                                   |
| ------- | ---------------------------------------------------------------------- |
| `jobs`  | [Array&lt;ImportPreviewJobForEntity&gt;](ImportPreviewJobForEntity.md) |
| `error` | Array&lt;string&gt;                                                    |

## Example

```typescript
import type { ImportPreviewJobsResult } from "";

// TODO: Update the object below with actual values
const example = {
  jobs: null,
  error: null,
} satisfies ImportPreviewJobsResult;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ImportPreviewJobsResult;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
