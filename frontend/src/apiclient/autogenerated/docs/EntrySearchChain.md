# EntrySearchChain

## Properties

| Name           | Type                           |
| -------------- | ------------------------------ |
| `entities`     | Array&lt;string&gt;            |
| `attrs`        | [Array&lt;Attr&gt;](Attr.md)   |
| `refers`       | [Array&lt;Refer&gt;](Refer.md) |
| `isAny`        | boolean                        |
| `hintItemName` | string                         |

## Example

```typescript
import type { EntrySearchChain } from "";

// TODO: Update the object below with actual values
const example = {
  entities: null,
  attrs: null,
  refers: null,
  isAny: null,
  hintItemName: null,
} satisfies EntrySearchChain;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntrySearchChain;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
