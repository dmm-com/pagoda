import {
  Full2HalfWidthConstant,
  Full2HalfWidthSourceRegex,
} from "services/Constants";

function toHalfWidth(origin: string): string {
  return origin.replace(new RegExp(Full2HalfWidthSourceRegex, "g"), (s) => {
    return String.fromCharCode(s.charCodeAt(0) - Full2HalfWidthConstant);
  });
}

export function normalizeToMatch(keyword: string): string {
  return toHalfWidth(keyword.normalize("NFKC").toLowerCase());
}

export function fuzzyMatch(text: string, keyword: string): boolean {
  const normalizedText = toHalfWidth(text.normalize("NFKC").toLowerCase());
  const normalizedKeyword = toHalfWidth(
    keyword.normalize("NFKC").toLowerCase(),
  );

  return normalizedText.indexOf(normalizedKeyword) !== -1;
}
