function convert_hierarchical_groups_to_tree_data(groups) {
  return groups.map(function(x) {
    children = convert_hierarchical_groups_to_tree_data(x.children);
    if (children.length > 0) {
      return {
        text: x.name,
        groupId: x.id,
        nodes: children,
        href: `/group/edit/${ x.id }`,
      }
    } else {
      return {
        text: x.name,
        groupId: x.id,
        href: `/group/edit/${ x.id }`,
      }
    }
  });
}

