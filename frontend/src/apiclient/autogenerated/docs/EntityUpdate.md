# EntityUpdate

## Properties

| Name                         | Type                                                                       |
| ---------------------------- | -------------------------------------------------------------------------- |
| `id`                         | number                                                                     |
| `name`                       | string                                                                     |
| `note`                       | string                                                                     |
| `itemNamePattern`            | string                                                                     |
| `itemNameType`               | string                                                                     |
| `isToplevel`                 | boolean                                                                    |
| `attrs`                      | [Array&lt;EntityAttrUpdate&gt;](EntityAttrUpdate.md)                       |
| `webhooks`                   | [Array&lt;WebhookCreateUpdate&gt;](WebhookCreateUpdate.md)                 |
| `isolationRules`             | [Array&lt;IsolationParentCreateUpdate&gt;](IsolationParentCreateUpdate.md) |
| `deleteChainExcludeEntities` | Array&lt;number&gt;                                                        |

## Example

```typescript
import type { EntityUpdate } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  note: null,
  itemNamePattern: null,
  itemNameType: null,
  isToplevel: null,
  attrs: null,
  webhooks: null,
  isolationRules: null,
  deleteChainExcludeEntities: null,
} satisfies EntityUpdate;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityUpdate;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
