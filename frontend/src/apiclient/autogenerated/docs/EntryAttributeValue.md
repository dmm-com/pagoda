# EntryAttributeValue

## Properties

| Name                 | Type                                                                                           |
| -------------------- | ---------------------------------------------------------------------------------------------- | -------- |
| `asObject`           | [EntryAttributeValueObject](EntryAttributeValueObject.md)                                      |
| `asString`           | string                                                                                         |
| `asNamedObject`      | [EntryAttributeValueNamedObject](EntryAttributeValueNamedObject.md)                            |
| `asArrayObject`      | [Array&lt;EntryAttributeValueObject&gt;](EntryAttributeValueObject.md)                         |
| `asArrayString`      | Array&lt;string&gt;                                                                            |
| `asArrayNamedObject` | [Array&lt;EntryAttributeValueNamedObjectBoolean&gt;](EntryAttributeValueNamedObjectBoolean.md) |
| `asArrayGroup`       | [Array&lt;EntryAttributeValueGroup&gt;](EntryAttributeValueGroup.md)                           |
| `asBoolean`          | boolean                                                                                        |
| `asGroup`            | [EntryAttributeValueGroup](EntryAttributeValueGroup.md)                                        |
| `asRole`             | [EntryAttributeValueRole](EntryAttributeValueRole.md)                                          |
| `asArrayRole`        | [Array&lt;EntryAttributeValueRole&gt;](EntryAttributeValueRole.md)                             |
| `asNumber`           | number                                                                                         |
| `asArrayNumber`      | Array&lt;number                                                                                | null&gt; |
| `asSelect`           | [EntryAttributeValueSelect](EntryAttributeValueSelect.md)                                      |
| `asMultiSelect`      | [Array&lt;EntryAttributeValueSelect&gt;](EntryAttributeValueSelect.md)                         |

## Example

```typescript
import type { EntryAttributeValue } from "";

// TODO: Update the object below with actual values
const example = {
  asObject: null,
  asString: null,
  asNamedObject: null,
  asArrayObject: null,
  asArrayString: null,
  asArrayNamedObject: null,
  asArrayGroup: null,
  asBoolean: null,
  asGroup: null,
  asRole: null,
  asArrayRole: null,
  asNumber: null,
  asArrayNumber: null,
  asSelect: null,
  asMultiSelect: null,
} satisfies EntryAttributeValue;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntryAttributeValue;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
