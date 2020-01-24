// Confirm deletion of data
function confirm_delete_table_item(e) {

  if(! $(this).attr('url')) {
    MessageBox.error('[ERROR] URL parameter is not specified, Please tell the Administrator to fix this problem');
    return;
  }

  if($(this).parent().parent().prop('tagName') != 'TR') {
    MessageBox.warning('You have to use this only for deleting a table item');
    return;
  }

  var elem_tr = $(this).parent().parent();
  if (window.confirm(CHECK_PHRASE)) {
    // set target button to be disabled to prevent sending duplicate requests
    $(this).prop('disabled', true);

    SendHttpPost($(this).attr('url')).done(function(data) {
      MessageBox.success(`Success to delete ${ data['name'] }`);
      elem_tr.remove();
    }).fail(function(data) {
      MessageBox.error(data.responseText);
    });
  }
}
