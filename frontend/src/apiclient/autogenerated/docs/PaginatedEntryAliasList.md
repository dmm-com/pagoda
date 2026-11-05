# PaginatedEntryAliasList

## Properties

| Name       | Type                                     |
| ---------- | ---------------------------------------- |
| `count`    | number                                   |
| `next`     | string                                   |
| `previous` | string                                   |
| `results`  | [Array&lt;EntryAlias&gt;](EntryAlias.md) |

## Example

```typescript
import type { PaginatedEntryAliasList } from ''

// TODO: Update the object below with actual values
const example = {
  "count": 123,
  "next": http://api.example.org/accounts/?offset=400&limit=100,
  "previous": http://api.example.org/accounts/?offset=200&limit=100,
  "results": null,
} satisfies PaginatedEntryAliasList

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PaginatedEntryAliasList
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
