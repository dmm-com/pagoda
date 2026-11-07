// Escape a value before it is handed to bootstrap-treeview, which inserts node
// text as HTML (jQuery .append), so that group/user names cannot inject markup.
function escape_tree_node_text(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function convert_hierarchical_groups_to_tree_data(groups) {
  return groups.map(function(x) {
    const children = convert_hierarchical_groups_to_tree_data(x.children);
    if (children.length > 0) {
      return {
        text: escape_tree_node_text(x.display_name || x.name),
        groupId: x.id,
        nodes: children,
        href: `/group/edit/${ x.id }`,
      }
    } else {
      return {
        text: escape_tree_node_text(x.display_name || x.name),
        groupId: x.id,
        href: `/group/edit/${ x.id }`,
      }
    }
  });
}
