var restore_entry = function(e) {
  if(confirm(`${ $(e.target).attr('entry_name') } を復旧させますか？`)) {
    $.ajax({
      type: 'POST',
      url: `/entry/do_restore/${ $(e.target).attr('entry_id') }/`,
      data: JSON.stringify({}),
      headers: {
        'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val()
      }
    }).done(function(data) {
      MessageBox.setNextOnLoadMessage(MessageBox.SUCCESS, data);
      location.reload();
    }).fail(function(data) {
      if (data.responseJSON['msg']) {
        MessageBox.setNextOnLoadMessage(MessageBox.ERROR, data.responseJSON['msg']);
      } else {
        MessageBox.setNextOnLoadMessage(MessageBox.ERROR, `Duplicate entry name <a href='/entry/show/${ data.responseJSON['entry_id'] }'>${ data.responseJSON['entry_name'] }</a>`);
      }
      location.reload();
    });
  }
}

var show_deleted_entry = function(e) {
  let entry_id = $(e.target).attr('entry_id');

  // reset attribute value that is read when user push submit button
  $('#modal_commit_restore').attr('entry_id', entry_id);
  $('#modal_commit_restore').attr('entry_name', $(e.target).text());

  // send a request to get attribute-values of specified entry
  $.ajax({
    type: 'GET',
    url: `/entry/api/v1/get_entry_info/${ entry_id }`,
  }).done(function(data) {
    reconstruct_modal_body_for_entry(data);

    // show actual modal body
    $('#modal_initial_body').hide();
    $('#modal_actual_body').show();
  });

  // send a request to get a job that deleted target entry
  $.ajax({
    type: 'GET',
    url: `/api/v1/job/search`,
    data: {
      'target_id': entry_id,
      'operation': {{ JOB.OPERATION.DELETE }},
    }
  }).done(function(data) {
    if(data.result.length > 0) {
      reconstruct_modal_body_for_job(data.result[0]);
    }
  });
}

var complete_processing = function(data) {
  var container = $('#entry_container');
  var counter = 0;

  container.empty();
  for (var entry of data['results']) {
    if(entry['status'] != 0) {
      continue;
    }

    var new_elem = $('<tr />');

    new_elem.append($(`<td><a class='show_deleted_entry' data-toggle="modal" data-target="#deleted_entry_info" href="#" entry_id="${ entry['id'] }">${entry['name']}</a></td>`));
    new_elem.append($(`<td><button type="button" class="btn btn-success btn-sm restore-item" entry_id="${ entry.id }" entry_name="${ entry.name }">Restore</button></td>`));

    // set event handlers
    new_elem.find('.restore-item').on('click', restore_entry);
    new_elem.find('.show_deleted_entry').on('click', show_deleted_entry);

    container.append(new_elem);
    counter++;
  }
  $('#entry_count').text(`エントリ数：${ data['results'].length }/{{ total_count }}`);
}

var search_entries = function(keyword) {
  $.ajax({
    type: 'GET',
    url: "/entry/api/v1/get_entries/{{ entity.id }}/",
    data: {
      keyword: keyword,
      is_active: 'False',
    },
  }).done(function(data){
    complete_processing(data);

    // reset sending flag
    sending_request = false;
  }).fail(function(data){
    MessageBox.error('failed to load data from server (Please reload this page or call Administrator)');
  });

  $('#entry_count').text('エントリ数：...データ取得中...');
}

var sending_request = false;
$(document).ready(function() {
  $("#narrow_down_entries").on('keyup', function(e) {
    if(! (e.keyCode != 13 || sending_request)) {
      sending_request = true;

      search_entries($(this).val());
    }
  });

  // set event handlers for this page
  $('.restore-item').on('click', restore_entry);
  $('.show_deleted_entry').on('click', show_deleted_entry);
  $('#modal_commit_restore').on('click', restore_entry);

  // set event handlers to export Entries of specified Entity
  $('.export_entry_with_yaml').on('click', send_export_request_yaml);
  $('.export_entry_with_csv').on('click', send_export_request_csv);

  // set event handler for modal window
  $('#deleted_entry_info').on('hidden.bs.modal', function(e) {
    $('#modal_initial_body').show();
    $('#modal_actual_body').hide();
  })

  var keyword = `{{ search_name }}`;
  if (keyword) {
    // This is the process when transitioning from the delete job
    sending_request = true;

    $("#narrow_down_entries").val(keyword);
    search_entries(keyword);
  }
});

function reconstruct_modal_body_for_job(job) {
  let elem_container = $('#modal_actual_body table .context_job');

  // clear old context
  elem_container.empty();

  elem_container.append(`<tr><td>Deleted by:</td><td>${ job.user }</td></tr>`);
  elem_container.append(`<tr><td>Deleted at:</td><td>${ job.updated_at }</td></tr>`);
}

function reconstruct_modal_body_for_entry(data) {
  let elem_container = $('#modal_actual_body table .context_attr');

  // clear old context
  elem_container.empty();

  for(let attr of data.attrs) {
    let elem_tr = $('<tr/>');
    let elem_td = $('<td/>');

    elem_tr.append($(`<td>${ attr.name }</td>`));

    if(attr.type == {{ attr_type.string }}) {
      elem_td.append($(`<span class='url_conv'>${ attr.value }</span>`));

    } else if(attr.type == {{ attr_type.entry }}) {
      if( attr.value ) {
        elem_td.append($(`<a href='/entry/show/${ attr.value.id }'>${ attr.value.name }</a>`));
      }

    } else if(attr.type == {{ attr_type.named_entry }}) {
      for(var key in attr.value ) {

        referral_info = '';
        if(attr.value[key] && attr.value[key].id) {
          referral_info = `<a href='/entry/show/${ attr.value[key].id }'>${ attr.value[key].name }</a>`;
        }

        elem_td.append($(`
          <div class='row'>
            <div class='col-3'>
              <span class='url_conv'>${ key }</span>
            </div>
            <div class='col-9'>${ referral_info }</div>
          </div>
        `));
      }

    } else if(attr.type == {{ attr_type.array_entry }}) {
      let elem_ul = $("<ul class='list-group'>");

      for(var info of attr.value ) {
        elem_ul.append($(`<li class='list-group-item'><a href='/entry/show/${ info.id }'>${ info.name }</li>`));
      }
      elem_td.append(elem_ul);

    } else if(attr.type == {{ attr_type.array_string }}) {
      let elem_ul = $("<ul class='list-group'>");

      for(var value of attr.value ) {
        elem_ul.append($(`<li class='list-group-item'>${ value }</li>`));
      }
      elem_td.append(elem_ul);

    } else if(attr.type == {{ attr_type.array_named_entry }}) {
      let elem_ul = $("<ul class='list-group'>");

      for(var value of attr.value ) {
        for(var key in value) {
          referral_info = '';
          if(value[key] && value[key].id) {
            referral_info = `<a href='/entry/show/${ value[key].id }'>${ value[key].name }</a>`;
          }

          elem_ul.append($(`
            <li class='list-group-item'>
              <div class='row'>
                <div class='col-3'>
                  <span class='url_conv'>${ key }</span>
                </div>
                <div class='col-9'>${ referral_info }</div>
              </div>
            </li>
          `));
        }
      }
      elem_td.append(elem_ul);

    } else if(attr.type == {{ attr_type.textarea }}) {
      elem_td.append($(`<span class='url_conv textarea'>${ attr.value }</span>`));

    } else if(attr.type == {{ attr_type.boolean }}) {
      if(attr.value) {
        elem_td.append($(`<input type="checkbox" disabled='True' checked='True'/>`));
      } else {
        elem_td.append($(`<input type="checkbox" disabled='True' />`));
      }

    } else if(attr.type == {{ attr_type.group }}) {
      elem_td.append($(`<a href='/group/'>${ attr.value.name }</a>`));

    } else if(attr.type == {{ attr_type.array_group }}) {
      let elem_ul = $("<ul class='list-group'>");

      for(var info of attr.value ) {
        elem_ul.append($(`<li class='list-group-item'><a href='/group/'>${ info.name }</li>`));
      }
      elem_td.append(elem_ul);

    } else if(attr.type == {{ attr_type.date }}) {
      elem_td.append($(`<span>${ attr.value }</span>`));
    }

    elem_tr.append(elem_td);
    elem_container.append(elem_tr);
  }
}
