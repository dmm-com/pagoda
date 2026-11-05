# PaginatedEntrySelfHistoryList

## Properties

| Name       | Type                                                 |
| ---------- | ---------------------------------------------------- |
| `count`    | number                                               |
| `next`     | string                                               |
| `previous` | string                                               |
| `results`  | [Array&lt;EntrySelfHistory&gt;](EntrySelfHistory.md) |

## Example

```typescript
import type { PaginatedEntrySelfHistoryList } from ''

// TODO: Update the object below with actual values
const example = {
  "count": 123,
  "next": http://api.example.org/accounts/?offset=400&limit=100,
  "previous": http://api.example.org/accounts/?offset=200&limit=100,
  "results": null,
} satisfies PaginatedEntrySelfHistoryList

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PaginatedEntrySelfHistoryList
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
