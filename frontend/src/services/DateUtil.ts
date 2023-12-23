export function formatDateTime(date: Date): string {
  return `${date.getFullYear()}/${
    date.getMonth() + 1
  }/${date.getDate()} ${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`;
}

export function formatDate(date: Date): string {
  return date.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export function setJSTdate(date: Date): Date {
  date.setHours(9, 0, 0, 0);
  return date;
}

export const DAY_OF_WEEK = {
  jp: ["日", "月", "火", "水", "木", "金", "土"],
};
