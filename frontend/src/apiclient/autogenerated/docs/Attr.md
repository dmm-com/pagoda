# Attr

## Properties

| Name     | Type             |
| -------- | ---------------- |
| `name`   | string           |
| `value`  | string           |
| `isAny`  | boolean          |
| `attrs`  | Array&lt;any&gt; |
| `refers` | Array&lt;any&gt; |

## Example

```typescript
import type { Attr } from "";

// TODO: Update the object below with actual values
const example = {
  name: null,
  value: null,
  isAny: null,
  attrs: null,
  refers: null,
} satisfies Attr;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as Attr;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
