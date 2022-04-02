function toHalfWidth(origin: string): string {
  return origin.replace(/[Ａ-Ｚａ-ｚ０-９]/g, (s) => {
    return String.fromCharCode(s.charCodeAt(0) - 0xfee0);
  });
}

export function fuzzyMatch(text: string, keyword: string): boolean {
  const normalizedText = toHalfWidth(text.toLowerCase());
  const normalizedKeyword = toHalfWidth(keyword.toLowerCase());

  return normalizedText.indexOf(normalizedKeyword) !== -1;
}
