interface GroupDisplayFields {
  name: string;
  displayName?: string;
}

export const getGroupDisplayName = (group: GroupDisplayFields): string =>
  group.displayName || group.name;
