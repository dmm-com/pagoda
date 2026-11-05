# EntityDiffAttribute

## Properties

| Name      | Type   |
| --------- | ------ |
| `id`      | number |
| `name`    | string |
| `type`    | number |
| `valueT0` | any    |
| `valueT1` | any    |

## Example

```typescript
import type { EntityDiffAttribute } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  type: null,
  valueT0: null,
  valueT1: null,
} satisfies EntityDiffAttribute;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityDiffAttribute;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
