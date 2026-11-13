// bootstrap-treeview inserts node text as HTML (jQuery .append), so group/user
// names must be escaped (escapeHtml is defined in http_request.js) before they
// are handed to it.
function escape_tree_node_text(value) {
  return escapeHtml(String(value));
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
