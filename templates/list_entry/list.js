var complete_processing = function(data) {
  var container = $('#entry_container');

  container.empty();
  for (var entry of data['results']) {
    var new_elem = $('<tr />');

    if(entry['status'] & {{ STATUS_ENTRY.CREATING }}) {
      new_elem.append($(`<td>${entry['name']} [作成中]</td>`));
    } else if(entry['status'] & {{ STATUS_ENTRY.EDITING }}) {
      new_elem.append($(`<td><a href="/entry/show/${entry['id']}/">${entry['name']} [編集中]</a></td>`));
    } else {
      new_elem.append($(`<td><a href="/entry/show/${entry['id']}/">${entry['name']}</a></td>`));
    }
    new_elem.append($(`<td><button type="button" class="btn btn-danger btn-sm del-item" url="/entry/do_delete/${ entry['id'] }/">del</button></td>`));
    new_elem.find('.del-item').on('click', confirm_delete_table_item);

    container.append(new_elem);
  }
  $('#entry_count').text(`エントリ数：${ data['results'].length }/{{ total_count }}`);
}

$(document).ready(function() {
  var sending_request = false;
  $('.del-item').on('click', confirm_delete_table_item);
  $("#narrow_down_entries").on('keyup', function(e) {
    if(! (e.keyCode != 13 || sending_request)) {
      sending_request = true;

      $.ajax({
        type: 'GET',
        url: "/entry/api/v1/get_entries/{{ entity.id }}/",
        data: {
          keyword: $(this).val(),
        },
      }).done(function(data){
        complete_processing(data);

        // reset sending flag
        sending_request = false
      }).fail(function(data){
        MessageBox.error('failed to load data from server (Please reload this page or call Administrator)');
      });

      $('#entry_count').text('エントリ数：...データ取得中...');
    }
  });

  // event handler to export Entries of specified Entity
  $('.export_entry_with_yaml').on('click', send_export_request_yaml);
  $('.export_entry_with_csv').on('click', send_export_request_csv);
});
