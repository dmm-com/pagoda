# ImportPreviewRow

## Properties

| Name                | Type                                                       |
| ------------------- | ---------------------------------------------------------- |
| `index`             | number                                                     |
| `kind`              | string                                                     |
| `name`              | string                                                     |
| `action`            | string                                                     |
| `reason`            | string                                                     |
| `changes`           | [Array&lt;ImportPreviewChange&gt;](ImportPreviewChange.md) |
| `willInvokeTrigger` | boolean                                                    |

## Example

```typescript
import type { ImportPreviewRow } from "";

// TODO: Update the object below with actual values
const example = {
  index: null,
  kind: null,
  name: null,
  action: null,
  reason: null,
  changes: null,
  willInvokeTrigger: null,
} satisfies ImportPreviewRow;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ImportPreviewRow;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
