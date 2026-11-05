# EntityDiff

## Properties

| Name    | Type                                             |
| ------- | ------------------------------------------------ |
| `count` | number                                           |
| `items` | [Array&lt;EntityDiffItem&gt;](EntityDiffItem.md) |

## Example

```typescript
import type { EntityDiff } from "";

// TODO: Update the object below with actual values
const example = {
  count: null,
  items: null,
} satisfies EntityDiff;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityDiff;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
