# EntryNetworkSearchResponse

## Properties

| Name        | Type                                                     |
| ----------- | -------------------------------------------------------- |
| `results`   | [Array&lt;EntryNetworkSearch&gt;](EntryNetworkSearch.md) |
| `hasMore`   | boolean                                                  |
| `totalHits` | number                                                   |

## Example

```typescript
import type { EntryNetworkSearchResponse } from "";

// TODO: Update the object below with actual values
const example = {
  results: null,
  hasMore: null,
  totalHits: null,
} satisfies EntryNetworkSearchResponse;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntryNetworkSearchResponse;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
