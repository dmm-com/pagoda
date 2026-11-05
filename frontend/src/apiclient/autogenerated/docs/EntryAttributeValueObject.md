# EntryAttributeValueObject

## Properties

| Name           | Type                                          |
| -------------- | --------------------------------------------- |
| `id`           | number                                        |
| `name`         | string                                        |
| `schema`       | [EntityAttributeType](EntityAttributeType.md) |
| `displayLabel` | string                                        |

## Example

```typescript
import type { EntryAttributeValueObject } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  schema: null,
  displayLabel: null,
} satisfies EntryAttributeValueObject;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntryAttributeValueObject;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
