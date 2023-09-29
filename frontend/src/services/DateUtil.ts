export function formatDateTime(date: Date): string {
  return `${date.getFullYear()}/${date.getMonth() + 1
    }/${date.getDate()} ${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`;
}

export function formatDate(date: Date): string {
  return date.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export function getJPNdate(date: Date): Date {
  date.setHours(date.getHours() + 9);
  return date;
}
