# ImportPreview

## Properties

| Name        | Type                                                 |
| ----------- | ---------------------------------------------------- |
| `summary`   | [ImportPreviewSummary](ImportPreviewSummary.md)      |
| `rows`      | [Array&lt;ImportPreviewRow&gt;](ImportPreviewRow.md) |
| `count`     | number                                               |
| `truncated` | boolean                                              |

## Example

```typescript
import type { ImportPreview } from "";

// TODO: Update the object below with actual values
const example = {
  summary: null,
  rows: null,
  count: null,
  truncated: null,
} satisfies ImportPreview;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ImportPreview;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
