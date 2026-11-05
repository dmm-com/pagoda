# EntryHistoryAttributeValue

## Properties

| Name          | Type                                          |
| ------------- | --------------------------------------------- |
| `id`          | number                                        |
| `type`        | number                                        |
| `createdTime` | Date                                          |
| `createdUser` | string                                        |
| `currValue`   | [EntryAttributeValue](EntryAttributeValue.md) |
| `prevValue`   | [EntryAttributeValue](EntryAttributeValue.md) |
| `prevId`      | number                                        |
| `parentAttr`  | [Attribute](Attribute.md)                     |

## Example

```typescript
import type { EntryHistoryAttributeValue } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  type: null,
  createdTime: null,
  createdUser: null,
  currValue: null,
  prevValue: null,
  prevId: null,
  parentAttr: null,
} satisfies EntryHistoryAttributeValue;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntryHistoryAttributeValue;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
