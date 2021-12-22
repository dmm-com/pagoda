function update_attr_condition(entities) {
  $.ajax({
    type: 'GET',
    url: `/api/v1/entity/attrs/${entities}`,
    dataType: 'json',
    contentType:   'application/x-www-form-urlencoded;charset=utf-8',
    scriptCharset: 'utf-8',
  }).done(function(data){
    var all_attr = $('#all_attr');
    var selected_attr = $('#selected_attr');

    all_attr.children().remove();
    selected_attr.children().remove();

    for(var attr_name of data['result']) {
      all_attr.append($(`<option value='${ attr_name }'>${ attr_name }</option>`));
    }

    $('#attr_condition').show();
  }).fail(function(msg){
    MessageBox.error(msg);
  });
}

function initialize_attr_condition() {
  // search all attrs which are selected and show form to set condition for attr
  target_entities = $('#selected_entity').children().map(function() { return this.value; });

  if(target_entities.length > 0) {
    update_attr_condition(target_entities.get().join());
  } else {
    $('#attr_condition').hide();
  }
}

/* handlers for specifying targets of entity */
$('#append_target_entity').on('click', function() {
  var elem_selected = $('#selected_entity');

  $("#all_entity").find(":selected").each(function(i, elem){
    if(elem_selected.find("option[value="+ $(elem).val() +"]").length == 0) {
      elem_selected.append($(elem).clone());
    }
  });

  initialize_attr_condition();
});

$('#delete_target_entity').on('click', function() {
  $("#selected_entity").find(":selected").each(function(i, elem){
    $(elem).remove();
  });

  initialize_attr_condition();
});

$('#append_target_attr').on('click', function() {
  var elem_selected = $('#selected_attr');

  $("#all_attr").find(":selected").each(function(i, elem){
    if(elem_selected.find(`option[value="${ $(elem).val() }"]`).length == 0) {
      elem_selected.append($(elem).clone());
    }
  });
});

$('#delete_target_attr').on('click', function() {
  $("#selected_attr").find(":selected").each(function(i, elem){
    $(elem).remove();
  });
});

$('.narrow_down_option').keyup(function() {
  var input_str = $(this).val();
  $(this).parent().find("option").each(function(i, elem){
    if($(elem).text().toUpperCase().indexOf(input_str.toUpperCase()) >= 0) {
      $(elem).show();
    } else {
      $(elem).hide();
    }
  });
});

$('#do_search').on('click', function() {
  var params = [];

  var entities = $('#selected_entity').children().map(function() {
    return 'entity[]=' + encodeURIComponent(this.value);
  }).get().join('&');

  var is_all_entities = $('#select_all_entity').is(':checked');
  if (is_all_entities){
    params.push('is_all_entities=true');
  } else {
    $('#selected_entity').children().map(function() {
      params.push('entity[]=' + encodeURIComponent(this.value));
    });
  }

  params.push('entry_name=');

  // Build URL encoded JSON stringified attrinfo
  const attrinfo = $('#selected_attr').children().map(function() {
    return {'name': this.value};
  }).get();
  params.push('attrinfo=' + encodeURIComponent(JSON.stringify(attrinfo)))

  var has_referral = $('#add_referral').is(':checked')
  if (has_referral){
    params.push('has_referral=true');
    params.push('referral_name=');
  }

  location.href = `/dashboard/advanced_search_result?${ params.join('&') }`;
});

$('#select_all_entity').on('click', function() {
  $('#all_entity').prop('disabled', $(this).is(':checked'));
  $('#selected_entity').prop('disabled', $(this).is(':checked'));

  if($(this).is(':checked')) {
    update_attr_condition(',');
  } else {
    initialize_attr_condition();
  }
});
