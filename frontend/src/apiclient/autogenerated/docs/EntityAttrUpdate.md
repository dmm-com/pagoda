# EntityAttrUpdate

## Properties

| Name              | Type                |
| ----------------- | ------------------- |
| `id`              | number              |
| `name`            | string              |
| `type`            | number              |
| `isMandatory`     | boolean             |
| `referral`        | Array&lt;number&gt; |
| `index`           | number              |
| `isSummarized`    | boolean             |
| `isDeleteInChain` | boolean             |
| `isDeleted`       | boolean             |
| `note`            | string              |
| `defaultValue`    | any                 |
| `choices`         | any                 |
| `nameOrder`       | number              |
| `namePrefix`      | string              |
| `namePostfix`     | string              |
| `displayAttr`     | string              |

## Example

```typescript
import type { EntityAttrUpdate } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  type: null,
  isMandatory: null,
  referral: null,
  index: null,
  isSummarized: null,
  isDeleteInChain: null,
  isDeleted: null,
  note: null,
  defaultValue: null,
  choices: null,
  nameOrder: null,
  namePrefix: null,
  namePostfix: null,
  displayAttr: null,
} satisfies EntityAttrUpdate;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityAttrUpdate;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
