# Webhook

## Properties

| Name                       | Type                                             |
| -------------------------- | ------------------------------------------------ |
| `id`                       | number                                           |
| `label`                    | string                                           |
| `url`                      | string                                           |
| `isEnabled`                | boolean                                          |
| `isVerified`               | boolean                                          |
| `verificationErrorDetails` | string                                           |
| `headers`                  | [Array&lt;WebhookHeaders&gt;](WebhookHeaders.md) |
| `isDeleted`                | boolean                                          |

## Example

```typescript
import type { Webhook } from "";

// TODO: Update the object below with actual values
const example = {
  id: null,
  label: null,
  url: null,
  isEnabled: null,
  isVerified: null,
  verificationErrorDetails: null,
  headers: null,
  isDeleted: null,
} satisfies Webhook;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as Webhook;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
