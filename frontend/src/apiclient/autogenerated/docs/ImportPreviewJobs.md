# ImportPreviewJobs

One preview job per model, mirroring the shape of the item import API.

## Properties

| Name     | Type                                                  |
| -------- | ----------------------------------------------------- |
| `result` | [ImportPreviewJobsResult](ImportPreviewJobsResult.md) |

## Example

```typescript
import type { ImportPreviewJobs } from "";

// TODO: Update the object below with actual values
const example = {
  result: null,
} satisfies ImportPreviewJobs;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ImportPreviewJobs;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
