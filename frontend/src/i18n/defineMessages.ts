/**
 * Declares a set of translated messages for one domain.
 * Both languages must define exactly the same keys; a missing or extra key
 * is reported as a type error.
 */
export function defineMessages<K extends string>(messages: {
  ja: Record<K, string>;
  en: Record<K, string>;
}): { ja: Record<K, string>; en: Record<K, string> } {
  return messages;
}
