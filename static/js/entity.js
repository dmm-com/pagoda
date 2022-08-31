var toggle_referral = function() {
  if($(this).val() & ATTR_TYPE.object || $(this).val() & ATTR_TYPE.named_object) {
    for(cls_name of ['attr_referral', 'list-group', 'narrow_down_referral']) {
      $(this).parent().parent().parent().find(`.${cls_name}`).show();
    }
  } else {
    for(cls_name of ['attr_referral', 'list-group', 'narrow_down_referral']) {
      $(this).parent().parent().parent().find(`.${cls_name}`).hide();
    }
  }
}

// This function update index of row for sorting them
var update_row_index = function() {
  $('#sortdata').find(".attr:not([deleted='true'])").each(function(index) {
    $(this).find('.row_index').val(index + 1);
  });
}

var del_attr = function() {
  var parent = $(this).parents(".attr");
  if(parent.attr('attr_id')) {
    parent.attr('deleted', true);
    parent.hide();
  } else {
    parent.remove();
  }

  // Re-sort row indexes
  update_row_index();
}

var validate_form = function() {
  var ok = true;

  // check if entity name is not empty
  var name_elem = $('input[name="name"]')
  ok = ok & check_not_empty(name_elem);

  // check attrs
  var attr_elems = $('tbody[name="attributes"]').find('tr.attr')
  attr_elems.map(function(index, dom) {
    var elem = $(dom);

    // check if attr name is not empty
    var attr_name_elem = elem.find('.attr_name');
    ok = ok & check_not_empty(attr_name_elem);

    // check if entry ref attr is specified for entry type
    var attr_type_elem = elem.find('.attr_type');
    if(ATTR_TYPE.object & attr_type_elem.val()) {
      var attr_referral_elem = elem.find('.attr_referral');
      var td_elem = attr_type_elem.parent().parent().parent();
      if(attr_referral_elem.val().length == 0) {
        td_elem.addClass('table-danger');
        ok = false;
      } else {
        td_elem.removeClass('table-danger');
      }
    }
  });
  return ok;
}

var check_not_empty = function(elem) {
  if(elem.val() == "") {
    elem.parent().addClass("table-danger");
    return false;
  }

  elem.parent().removeClass("table-danger");
  return true;
}

function enable_input() {
  ['input', 'select', 'button', 'tr'].forEach(function(tag) {
    $(tag).prop('disabled', false);
  });
  $('body').css('cursor', 'auto');
  $('#sortdata').sortable('enable');
}

function disable_input() {
  ['input', 'select', 'button', 'tr'].forEach(function(tag) {
    $(tag).prop('disabled', true);
  });
  $('body').css('cursor', 'wait');
  $('#sortdata').sortable('disable');
}

function initialize_tooltips() {
  $('.attr_option_mandatory').prop('title', gettext('entity_edit_desc_mandatory')).tooltip();
  $('.attr_option_delete_in_chain').prop('title', gettext('entity_edit_desc_delete_in_chain')).tooltip();

  $('[data-toggle="tooltip"]').on('click', function(e) {
    let tgt_elem = $(e.target)
    if (tgt_elem.prop('tagName') == 'SPAN') {
      input_elem = tgt_elem.find('input');

      if (input_elem.prop('checked')) {
        input_elem.prop('checked', false);
      } else {
        input_elem.prop('checked', true);
      }
    }
  });
}

$('#edit-form').submit(function(event){
  if(!validate_form()) {
    MessageBox.error("Some parameters are required to input");
    return false;
  }

  var sending_data = Object.assign(parseJson($(this).serializeArray()), {
    'attrs': $('.attr').map(function(index, elem){
      var ret = {
        'name': $(this).find('.attr_name').val(),
        'type': $(this).find('.attr_type').val(),
        'is_mandatory': $(this).find('.is_mandatory:checked').val() != undefined ? true : false,
        'is_delete_in_chain': $(this).find('.is_delete_in_chain:checked').val() != undefined ? true : false,
        'ref_ids': $(this).find('.attr_referral').val(),
        'row_index': $(this).find('.row_index').val(),
      };
      if($(this).attr('attr_id')) {
        ret['id'] = $(this).attr('attr_id');
        if($(this).attr('deleted')) {
          ret['deleted'] = true;
        }
      }
      return ret;
    }).get(),
    'is_not_indexed': $('input[name=is_not_indexed]:checked').val() !== undefined,
    'is_toplevel': $('input[name=is_toplevel]:checked').val() !== undefined,
  });

  // disable all input parameter to specify sending request
  disable_input();

  /*
   * We want to disable all input element after getting values from them. So we call ajax method
   * directly instead of using wrapper because some values couldn't be get from selector once they
   * are disabled in some environment (e.g. Google Chrome).
   */
  $.ajax({
    url:           $(this).attr('url'),
    type:          'post',
    dataType:      'json',
    contentType:   'application/x-www-form-urlencoded;charset=utf-8',
    scriptCharset: 'utf-8',
    headers: {
      'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val(),
    },
    data:          JSON.stringify(sending_data)
  }).done(function(data) {
    // set successful message to the updated page
    MessageBox.setNextOnLoadMessage(MessageBox.SUCCESS, data.msg);

    // redirect to the entity list page
    location.href = `/entry/${ data.entity_id }`;
  }).fail(function(data) {
    MessageBox.error(data.responseText);

    // reset all input parameter to be able to input
    enable_input();
  });

  return false;
});
$('.attr_type').change(toggle_referral);

var append_attr_column = function() {
  var new_column = $('[name=attr_template]').clone();

  // clear template meta info
  new_column.removeAttr('name');
  new_column.find(".attr_referral").removeClass('template');
  new_column.addClass('attr');

  new_column.show();
  new_column.find('.attr_type').on('change', toggle_referral);
  new_column.find('.narrow_down_referral').on(narrow_down_handler);
  new_column.find('button[name=del_attr]').on('click', del_attr);
  new_column.find(".attr_referral").on('change', update_selected_referral);

  $('[name=attributes]').append(new_column);

  // Re-sort row indexes and toltip display and event handler
  update_row_index();
  initialize_tooltips();
}

var bind_del_attr = function(column) {
  $("button[name=del_attr]").on('click', function() {
    var parent = $(this).parents(".attr");
    if(parent.attr('attr_id')) {
      parent.attr('deleted', true);
      parent.hide();
    } else {
      parent.remove();
    }

    // Re-sort row indexes
    update_row_index();
  });
};

var update_option = function(select_elem) {
  var input_str = $(select_elem).val();
  $(select_elem).parent().parent().find('select option').each(function(i, elem) {
    if($(elem).val() != 0) {
      if($(elem).text().toLowerCase().indexOf(input_str.toLowerCase()) >= 0) {
        $(elem).show();
      } else {
        $(elem).hide();
      }
    }
  });
}
var enable_key_handling = true;
var narrow_down_handler = {
  "compositionstart": function() {
    enable_key_handling = false;
  },
  "compositionend": function() {
    enable_key_handling = true;

    update_option(this);
  },
  "keyup": function(e) {
    var is_BS = (e.keyCode == 8);

    if (!(!enable_key_handling || !(/[a-zA-Z0-9 -/:-@\[-~]/.test($(this).val) || is_BS))) {
      update_option(this);
    }
  }
}

function initialize_entries_list() {
  // Get information for each entity at background processing to be fast to load page.
  $.ajax({
    url: '/entity/api/v1/get_entities',
    type: 'GET',
    dataType: 'json',
    contentType: 'application/x-www-form-urlencoded;charset=utf-8',
    scriptCharset: 'utf-8',
    headers: {
      'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val(),
    },
  }).done(function(data) {
    $('.attr_referral').each(function(i, select) {
      for(info of data['entities']) {
        var is_append = true;
        $(select).children('option').each(function(j, option){
          if(info['id'] == $(option).val()) {
            is_append = false;
            return;
          }
        });

        if(is_append) {
          var new_option = $(`<option value=${ info['id'] }>${ info['name'] }</option>`);
          if(! $(select).hasClass('template')) {
            new_option.hide();
          }
          $(select).append(new_option);
        }
      }
    });
  });
}

var update_selected_referral = function() {
  var list_group = $(this).parent().find('ul');
  list_group.empty();

  $(this).find('option:selected').each(function(e) {
    if($(this).val() > 0) {
      new_elem = $("<li class='list-group-item list-group-item-info' style='height: 30px; padding: 5px 15px;' />");
      new_elem.text($(this).text());

      list_group.append(new_elem);
    }
  });
}

$(document).ready(function() {
  $('#sortdata').sortable();

  $('#sortdata').on('sortstop', update_row_index);
  $("button[name=del_attr]").on('click', del_attr);
  $(".narrow_down_referral").on(narrow_down_handler);
  $(".attr_referral").on('change', update_selected_referral);

  $('button[name=add_attr]').on('click', function() {
    append_attr_column();
    return false;
  });

  initialize_entries_list();

  // this initialize all tooltip display and hover/click processing
  initialize_tooltips();
});
