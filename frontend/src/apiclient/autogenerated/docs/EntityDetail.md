# EntityDetail

## Properties

| Name                         | Type                                                                                                       |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `id`                         | number                                                                                                     |
| `name`                       | string                                                                                                     |
| `note`                       | string                                                                                                     |
| `itemNamePattern`            | string                                                                                                     |
| `itemNameType`               | string                                                                                                     |
| `status`                     | number                                                                                                     |
| `isToplevel`                 | boolean                                                                                                    |
| `attrs`                      | [Array&lt;EntityDetailAttribute&gt;](EntityDetailAttribute.md)                                             |
| `webhooks`                   | [Array&lt;Webhook&gt;](Webhook.md)                                                                         |
| `isolationRules`             | [Array&lt;IsolationParent&gt;](IsolationParent.md)                                                         |
| `isPublic`                   | boolean                                                                                                    |
| `hasOngoingChanges`          | boolean                                                                                                    |
| `permission`                 | number                                                                                                     |
| `deleteChainExcludeEntities` | [Array&lt;EntityDetailDeleteChainExcludeEntitiesInner&gt;](EntityDetailDeleteChainExcludeEntitiesInner.md) |

## Example

```typescript
import type { EntityDetail } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  name: null,
  note: null,
  itemNamePattern: null,
  itemNameType: null,
  status: null,
  isToplevel: null,
  attrs: null,
  webhooks: null,
  isolationRules: null,
  isPublic: null,
  hasOngoingChanges: null,
  permission: null,
  deleteChainExcludeEntities: null,
} satisfies EntityDetail;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as EntityDetail;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
