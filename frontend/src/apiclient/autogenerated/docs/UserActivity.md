# UserActivity

## Properties

| Name         | Type                    |
| ------------ | ----------------------- |
| `actionType` | string                  |
| `targetType` | string                  |
| `target`     | { [key: string]: any; } |
| `timestamp`  | Date                    |

## Example

```typescript
import type { UserActivity } from "";

// TODO: Update the object below with actual values
const example = {
  actionType: null,
  targetType: null,
  target: null,
  timestamp: null,
} satisfies UserActivity;

console.log(example);

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example);
console.log(exampleJSON);

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as UserActivity;
console.log(exampleParsed);
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)
