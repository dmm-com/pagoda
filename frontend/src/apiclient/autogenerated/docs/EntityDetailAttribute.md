# EntityDetailAttribute

## Properties

| Name              | Type                                 |
| ----------------- | ------------------------------------ |
| `id`              | number                               |
| `index`           | number                               |
| `name`            | string                               |
| `type`            | number                               |
| `isMandatory`     | boolean                              |
| `isDeleteInChain` | boolean                              |
| `isSummarized`    | boolean                              |
| `isWritable`      | boolean                              |
| `referral`        | Array&lt;{ [key: string]: any; }&gt; |
| `note`            | string                               |
| `defaultValue`    | any                                  |
| `choices`         | any                                  |
| `choicesInUse`    | Array&lt;string&gt;                  |
| `nameOrder`       | number                               |
| `namePrefix`      | string                               |
| `namePostfix`     | string                               |
| `displayAttr`     | string                               |

## Example

```typescript
import type { EntityDetailAttribute } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  index: null,
  name: null,
  type: null,
  isMandatory: null,
  isDeleteInChain: null,
  isSummarized: null,
  isWritable: null,
  referral: null,
  note: null,
  defaultValue: null,
  choices: null,
  choicesInUse: null,
  nameOrder: null,
  namePrefix: null,
  namePostfix: null,
  displayAttr: null,
} satisfies EntityDetailAttribute;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityDetailAttribute;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
