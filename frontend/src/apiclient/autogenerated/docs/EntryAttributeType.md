# EntryAttributeType

## Properties

| Name          | Type                                          |
| ------------- | --------------------------------------------- |
| `id`          | number                                        |
| `type`        | number                                        |
| `isMandatory` | boolean                                       |
| `isReadable`  | boolean                                       |
| `value`       | [EntryAttributeValue](EntryAttributeValue.md) |
| `schema`      | [EntityAttributeType](EntityAttributeType.md) |

## Example

```typescript
import type { EntryAttributeType } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  type: null,
  isMandatory: null,
  isReadable: null,
  value: null,
  schema: null,
} satisfies EntryAttributeType;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntryAttributeType;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
