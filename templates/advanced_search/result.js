function make_attr_elem(attr, hint_attr) {
  var new_elem = $(`<td id=${ hint_attr }/>`);

  function get_named_column(value) {
    var key = Object.keys(value)[0];
    var ref_value = value[key];

    var value_str = '';
    if (ref_value) {
      value_str = `<a href='/entry/show/${ ref_value.id }'>${ ref_value.name }</a>`;
    }

    return `<div class='row'> \
              <div class='col'> \
                <p class='url_conv'>${ key }</p> \
              </div> \
              <div class='col'>${ value_str }</div> \
            </div>`;
  }

  if (attr && attr.value) {
    switch (attr.type) {
      case {{ attr_type.string }}:
      case {{ attr_type.textarea }}:
      case {{ attr_type.boolean }}:
      case {{ attr_type.date }}:
        new_elem.text(attr.value);
        break;

      case {{ attr_type.entry }}:
        if (attr.value) {
          new_elem.append($(`<a href='/entry/show/${ attr.value.id }'>${ attr.value.name }</a>`));
        }
        break;

      case {{ attr_type.group }}:
        if (attr.value) {
          new_elem.append($(`<a href='/group/'>${ attr.value.name }</a>`));
        }
        break;

      case {{ attr_type.named_entry }}:
        new_elem.append($(get_named_column(attr.value)));
        break;

      case {{ attr_type.array_string }}:
        var elem_ul = $("<ul class='list-group'/>");
        for(var value of attr.value) {
          elem_ul.append($(`<li class='list-group-item'>${ value }</li>`));
        }
        new_elem.append(elem_ul);
        break;

      case {{ attr_type.array_entry }}:
        var elem_ul = $("<ul class='list-group'/>");
        for(var value of attr.value) {
          if(value) {
            elem_ul.append($(`<li class='list-group-item'><a href='/entry/show/${ value.id }'>${ value.name }</a></li>`));
          } else {
            elem_ul.append($(`<li class='list-group-item' />`));
          }
        }
        new_elem.append(elem_ul);
        break;

      case {{ attr_type.array_named_entry }}:
        var elem_ul = $("<ul class='list-group'/>");
        for(var value of attr.value) {
          elem_ul.append($(`<li class='list-group-item'>${ get_named_column(value) }</li>`));
        }
        new_elem.append(elem_ul);
        break;

      case {{ attr_type.array_group }}:
        var elem_ul = $("<ul class='list-group'/>");
        for(var value of attr.value) {
          if(value) {
            elem_ul.append($(`<li class='list-group-item'><a href='/group/'>${ value.name }</a></li>`));
          } else {
            elem_ul.append($(`<li class='list-group-item' />`));
          }
        }
        new_elem.append(elem_ul);
        break;
    }
  }

  return new_elem;
}

function reconstruct_tbody(results) {
  var elem_parent = $('#main_table');

  // First of all, clear tbody
  elem_parent.children().remove();

  for(var result of results) {
    var new_elem_entry = $('<tr/>');

    new_elem_entry.append(`<th id=entry_name><a href='/entry/show/${ result.entry.id }/'>${ result.entry.name } [${ result.entity.name}]</a></th>`);

    {% for hint_attr in hint_attrs %}
      new_elem_entry.append(make_attr_elem(result.attrs['{{ hint_attr.name }}'], '{{ hint_attr.name }}'));
    {% endfor %}

    {% if has_referral %}
      let elem_ref_td = $('<td id=referral />');
      let elem_ref_ul = $("<ul class='list-group'/>");

      for(let ref of result.referrals) {
        elem_ref_ul.append($(`<li class='list-group-item'><a href='/entry/show/${ ref.id }'>${ ref.name } / ${ ref.schema }</a></li>`));
      }

      elem_ref_td.append(elem_ref_ul)
      new_elem_entry.append(elem_ref_td);
    {% endif %}

    elem_parent.append(new_elem_entry);
  }
}

$(document).ready(function() {
  var sending_request = false;
  var entities = '{{ entities }}';

  function get_attrinfo() {
    ret_value = $('.hint_attr_value').map(function() {
      return {
        'name': $(this).attr('attrname'),
        'keyword': $(this).val(),
      }
    }).get();

    return ret_value;
  }

  function narrow_results_down(e) {
    if(! (e.keyCode != 13 || sending_request)) {
      sending_request = true;

      $('#entry_count').text('(...処理中...)');

      request_params = {
          entities: '{{ entities }}'.split(','),
          entry_name: $('.hint_entry_name').val(),
          attrinfo: get_attrinfo(),
      };

      {% if has_referral %}
      request_params['referral'] = $('.narrow_down_referral').val();
      {% endif %}

      if($('#check_search_all').is(':checked')) {
        request_params['entry_limit'] = 99999;
      }

      $.ajax({
        type: 'POST',
        url: "/api/v1/entry/search",
        data: JSON.stringify(request_params),
        dataType:      'json',
        contentType:   'application/json;charset=utf-8',
        scriptCharset: 'utf-8',
        headers: {
          'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val(),
        },
      }).done(function(data){
        sending_request = false;

        $('#entry_count').text(`(${ data.result.ret_count } 件)`);

        reconstruct_tbody(data.result.ret_values);

        // preserve a permalnk via pushState API to the advanced_search view (not entry-search API)
        // to filter search results with attribute keywords
        let params = [];
        for (const entity of '{{ entities }}'.split(',')) {
            params.push('entity[]=' +  entity);
        }
        params.push('entry_name=' + $('.hint_entry_name').val());
        params.push('attrinfo=' + encodeURIComponent(JSON.stringify(get_attrinfo())));
        {% if has_referral %}
        params.push('has_referral=' + $('.narrow_down_referral').val());
        {% endif %}
        window.history.pushState('', '', 'advanced_search_result?' + params.join('&'));

      }).fail(function(data){
        MessageBox.error(data.responseText);
      });
    }
  }

  function update_modal_attr_list(e) {
    var elem_selector = $('#modal_condition_all_attr');

    if(elem_selector.is('[disabled]')) {
      let entities = '{{ entities }}';
      {% if is_all_entities %}
        entities = ',';
      {% endif %}

      $.ajax({
        type: 'GET',
        url: `/api/v1/entity/attrs/${ entities }`,
        dataType: 'json',
        contentType:   'application/x-www-form-urlencoded;charset=utf-8',
        scriptCharset: 'utf-8',
      }).done(function(data){
        // Update modal_condition_all_attr optinos
        elem_selector.children().remove();
        elem_selector.removeAttr('disabled');

        for(let name of data['result']) {
          elem_selector.append($(`<option value='${ name }'>${ name }</option>`));
        }
      }).fail(function(msg){
        MessageBox.error(msg);
      });
    }
  }

  function submit_export(style) {
    MessageBox.clear();

    $.ajax({
      type: 'post',
      url: '/dashboard/advanced_search_export',
      data: JSON.stringify({
        'entities': '{{ entities }}'.split(','),
        'attrinfo': get_attrinfo(),
        'entry_name': $('.hint_entry_name').val(),
        'has_referral': $('.narrow_down_referral').val(),
        'export_style': style,
      }),
      dataType:      'json',
      contentType:   'application/json;charset=utf-8',
      scriptCharset: 'utf-8',
      headers: {
        'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val(),
      },
    }).done(function(data) {
      MessageBox.success(data.result);

    }).fail(function(data) {
      MessageBox.error(data.responseText);
    });
  }

  $(".narrow_down_referral").on('keyup', narrow_results_down);
  $(".narrow_down_entries").on('keyup', narrow_results_down);

  $('.export_yaml').on('click', function(e) { submit_export('yaml'); });
  $('.export_csv').on('click', function(e) { submit_export('csv'); });

  /*
   * These are event handlers for the modal window of updating search attribute condition.
   */
  $('#show_renew_search_attr_condition').on('click', update_modal_attr_list);
  $('#modal_condition_narrow_down').keyup(function() {
    var input_str = $(this).val();
    $(this).parent().find("option").each(function(i, elem){
      if($(elem).text().toUpperCase().indexOf(input_str.toUpperCase()) >= 0) {
        $(elem).show();
      } else {
        $(elem).hide();
      }
    });
  });
  $('.modal_cond_update_attr').on('click', function(e) {
    let elem_selected = $('#modal_condition_selected_attr');

    if ($(e.target).hasClass('append_attr')) {
      // Here is append processing to add selected items to selector
      $("#modal_condition_all_attr").find(":selected").each(function(i, elem){
        if(elem_selected.find(`option[value="${ $(elem).val() }"]`).length == 0) {
          elem_selected.append($(elem).clone());
        }
      });
    } else {
      // Here is delete processing to remove selected items of selector
      elem_selected.find(":selected").each(function(i, elem){
        $(elem).remove();
      });
    }
  });
  $('#commit_condition_change').on('click', function(e) {
    var params = [];

    // set get parameters
    params.push(`is_all_entities=${ '{{ is_all_entities }}'.toLowerCase() }`);
    params.push(`has_referral=${ $('#modal_cond_add_referral').is(':checked') }`);

    '{{ entities }}'.split(',').forEach(function(val) {
      params.push(`entity[]=${ val }`);
    });

    $('#modal_condition_selected_attr').find('option').each(function(i, elem) {
      params.push(`attr[]=${ encodeURIComponent($(elem).val()) }`);
    });

    location.href = `/dashboard/advanced_search_result?${ params.join('&') }`;
  });
});
