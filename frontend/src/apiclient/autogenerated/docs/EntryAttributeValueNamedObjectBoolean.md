# EntryAttributeValueNamedObjectBoolean

## Properties

| Name       | Type                                                      |
| ---------- | --------------------------------------------------------- |
| `name`     | string                                                    |
| `object`   | [EntryAttributeValueObject](EntryAttributeValueObject.md) |
| `_boolean` | boolean                                                   |

## Example

```typescript
import type { EntryAttributeValueNamedObjectBoolean } from "";

// TODO: Update the object below with actual values
const example = {
  name: null,
  object: null,
  _boolean: null,
} satisfies EntryAttributeValueNamedObjectBoolean;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(
  exampleJSON,
) as EntryAttributeValueNamedObjectBoolean;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
