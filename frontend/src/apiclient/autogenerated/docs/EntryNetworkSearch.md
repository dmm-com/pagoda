# EntryNetworkSearch

## Properties

| Name      | Type                                                               |
| --------- | ------------------------------------------------------------------ |
| `id`      | number                                                             |
| `name`    | string                                                             |
| `schema`  | [Entity](Entity.md)                                                |
| `matches` | [Array&lt;EntryNetworkSearchMatch&gt;](EntryNetworkSearchMatch.md) |

## Example

```typescript
import type { EntryNetworkSearch } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  schema: null,
  matches: null,
} satisfies EntryNetworkSearch;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntryNetworkSearch;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
