# PaginatedGroupList

## Properties

| Name       | Type                           |
| ---------- | ------------------------------ |
| `count`    | number                         |
| `next`     | string                         |
| `previous` | string                         |
| `results`  | [Array&lt;Group&gt;](Group.md) |

## Example

```typescript
import type { PaginatedGroupList } from ''

// TODO: Update the object below with actual values
const example = {
  "count": 123,
  "next": http://api.example.org/accounts/?page=4,
  "previous": http://api.example.org/accounts/?page=2,
  "results": null,
} satisfies PaginatedGroupList

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PaginatedGroupList
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
