# ImportPreviewSummary

## Properties

| Name        | Type   |
| ----------- | ------ |
| `created`   | number |
| `updated`   | number |
| `unchanged` | number |
| `skipped`   | number |
| `errored`   | number |
| `total`     | number |

## Example

```typescript
import type { ImportPreviewSummary } from "";

// TODO: Update the object below with actual values
const example = {
  created: null,
  updated: null,
  unchanged: null,
  skipped: null,
  errored: null,
  total: null,
} satisfies ImportPreviewSummary;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ImportPreviewSummary;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
