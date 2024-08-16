function make_attr_elem(attr, hint_attr) {
  var new_elem = $(`<td id=${ hint_attr }/>`);

  function get_named_column(value) {
    var key = Object.keys(value)[0];
    var ref_value = value[key];

    var value_str = '';
    if (ref_value) {
      value_str = `<a href='/entry/show/${ ref_value.id }/'>${ ref_value.name }</a>`;
    }

    return `<div class='row'> \
              <div class='col'> \
                <p class='url_conv'>${ key ?? '' }</p> \
              </div> \
              <div class='col'>${ value_str }</div> \
            </div>`;
  }

  if (attr && attr.is_readable == false) {
    new_elem.append("Permission denied.");
    new_elem.addClass('table-secondary');
    return new_elem;
  }

  if (attr && attr.type) {
    switch (attr.type) {
      case {{ attr_type.string }}:
      case {{ attr_type.textarea }}:
      case {{ attr_type.boolean }}:
      case {{ attr_type.date }}:
        new_elem.text(attr.value);
        break;

      case {{ attr_type.object }}:
        if (attr.value) {
          new_elem.append($(`<a href='/entry/show/${ attr.value.id }/'>${ attr.value.name }</a>`));
        }
        break;

      case {{ attr_type.group }}:
        if (attr.value) {
          new_elem.append($(`<a href='/group/'>${ attr.value.name }</a>`));
        }
        break;

      case {{ attr_type.role }}:
        if (attr.value) {
          new_elem.append($(`<a href='/role/edit/${ attr.value.id }'>${ attr.value.name }</a>`));
        }
        break;

      case {{ attr_type.named_object }}:
        new_elem.append($(get_named_column(attr.value)));
        break;

      case {{ attr_type.array_string }}:
        var elem_ul = $("<ul class='list-group'/>");
        for(var value of attr.value) {
          elem_ul.append($(`<li class='list-group-item'>${ value }</li>`));
        }
        new_elem.append(elem_ul);
        break;

      case {{ attr_type.array_object }}:
        var elem_ul = $("<ul class='list-group'/>");
        for(var value of attr.value) {
          if(value) {
            elem_ul.append($(`<li class='list-group-item'><a href='/entry/show/${ value.id }/'>${ value.name }</a></li>`));
          } else {
            elem_ul.append($(`<li class='list-group-item' />`));
          }
        }
        new_elem.append(elem_ul);
        break;

      case {{ attr_type.array_named_object }}:
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

      case {{ attr_type.array_role }}:
        var elem_ul = $("<ul class='list-group'/>");
        for(var value of attr.value) {
          if(value) {
            elem_ul.append($(`<li class='list-group-item'><a href='/role/edit/${ value.id }'>${ value.name }</a></li>`));
          } else {
            elem_ul.append($(`<li class='list-group-item' />`));
          }
        }
        new_elem.append(elem_ul);
        break;
    }
  } else {
    new_elem.addClass('table-secondary');
  }

  return new_elem;
}

function reconstruct_tbody(results) {
  var elem_parent = $('#main_table');

  // First of all, clear tbody
  elem_parent.children().remove();

  for(var result of results) {
    var new_elem_entry = $('<tr id=entryinfo/>');

    new_elem_entry.append(`<th id=entry_name><a href='/entry/show/${ result.entry.id }/'>${ result.entry.name } [${ result.entity.name}]</a></th>`);

    {% for hint_attr in hint_attrs %}
      if(result.is_readable == false){
        new_elem_entry.append("<td class='table-secondary' id='{{ hint_attr.name }}'>Permission denied.</td>");
      }else{
        new_elem_entry.append(make_attr_elem(result.attrs['{{ hint_attr.name }}'], '{{ hint_attr.name }}'));
      }
    {% endfor %}

    {% if has_referral%}
      let elem_ref_td = $('<td id=referral />');
      let elem_ref_ul = $("<ul class='list-group'/>");

      for(let ref of result.referrals) {
        elem_ref_ul.append($(`<li class='list-group-item'><a href='/entry/show/${ ref.id }/'>${ ref.name } / ${ ref.schema.name }</a></li>`));
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
      if ($(this).val()){
        return {
          'name': $(this).attr('attrname'),
          'keyword': $(this).val(),
        }
      } else {
        return {
          'name': $(this).attr('attrname')
        }
      }
    }).get();

    return ret_value;
  }

  function narrow_results_down(e) {
    if(! (e.keyCode != 13 || sending_request)) {
      sending_request = true;
      MessageBox.clear();
      $('#entry_count').text('(...処理中...)');

      request_params = {
          entities: '{{ entities }}'.split(','),
          entry_name: $('.hint_entry_name').val(),
          attrinfo: get_attrinfo(),
          is_output_all: false,
      };

      {% if has_referral%}
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
        {% if is_all_entities %}
        params.push('is_all_entities=true');
        {% else %}
        '{{ entities }}'.split(',').forEach(function(val) {
          params.push('entity[]=' + val);
        });
        {% endif %}
        params.push('entry_name=' + $('.hint_entry_name').val());
        params.push('attrinfo=' + encodeURIComponent(JSON.stringify(get_attrinfo())));
        {% if has_referral %}
        params.push('has_referral=true');
        params.push('referral_name=' + $('.narrow_down_referral').val());
        {% endif %}
        window.history.pushState('', '', 'advanced_search_result?' + params.join('&'));

      }).fail(function(data){
        sending_request = false;
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
        'has_referral': $('.narrow_down_referral').val() !== undefined,
        'referral_name': $('.narrow_down_referral').val(),
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
    if ('{{ is_all_entities }}' === 'True'){
      params.push('is_all_entities=' + '{{ is_all_entities }}'.toLowerCase());
    } else {
      '{{ entities }}'.split(',').forEach(function(val) {
        params.push('entity[]=' + val);
      });
    }

    params.push(`entry_name=${$('.hint_entry_name').val()}`)

    const attrinfo = $('#modal_condition_selected_attr').find('option').map(function() {
      var hint_attr_value = $(`.hint_attr_value[attrname="${this.value }"]`).val()
      if (hint_attr_value){
        return {'name': this.value, 'keyword': hint_attr_value};
      } else {
        return {'name': this.value};
      }
    }).get();
    params.push('attrinfo=' + encodeURIComponent(JSON.stringify(attrinfo)));

    if ($('#modal_cond_add_referral').is(':checked')){
      params.push('has_referral=true');
      params.push(`referral_name=${$('.narrow_down_referral').val() || ''}`);
    }

    location.href = `/dashboard/advanced_search_result?${ params.join('&') }`;
  });
});
