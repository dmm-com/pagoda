export const AclNameById = (id: number): string | null => {
  switch (id) {
    case 1:
      return "権限なし";
    case 2:
      return "閲覧";
    case 4:
      return "閲覧・編集";
    case 8:
      return "閲覧・編集・削除";
  }

  return null;
};
