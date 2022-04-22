import {
  Full2HalfWidthConstant,
  Full2HalfWidthSourceRegex,
} from "utils/Constants";

function toHalfWidth(origin: string): string {
  return origin.replace(new RegExp(Full2HalfWidthSourceRegex, "g"), (s) => {
    return String.fromCharCode(s.charCodeAt(0) - Full2HalfWidthConstant);
  });
}

export function normalizeToMatch(keyword: string): string {
  return toHalfWidth(keyword.toLowerCase());
}

export function fuzzyMatch(text: string, keyword: string): boolean {
  const normalizedText = toHalfWidth(text.toLowerCase());
  const normalizedKeyword = toHalfWidth(keyword.toLowerCase());

  return normalizedText.indexOf(normalizedKeyword) !== -1;
}
