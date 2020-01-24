var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
function csrfSafeMethod(method) {
  // these HTTP methods do not require CSRF protection
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  }
});

// Primitive function to send HTTP Post request
SendHttpPost = function(url, params={}) {
  return $.ajax({
    url:           url,
    type:          'post',
    dataType:      'json',
    contentType:   'application/x-www-form-urlencoded;charset=utf-8',
    scriptCharset: 'utf-8',
    headers: {
      'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val(),
    },
    data:          JSON.stringify(params)
  });
}

// This sends HTTP POST request and reloads page
HttpPost = function(form_elem, add_data={}) {
  // parse form data to JSON object
  var sending_data = parseJson(form_elem.serializeArray());  

  // merge additional object to the form data if needed
  if(add_data != undefined && typeof add_data == 'object') {
    sending_data = Object.assign(sending_data, add_data);
  }

  return SendHttpPost(form_elem.attr('url'), sending_data);
}

var parseJson = function(data) {
  var returnJson = {};
  for (idx = 0; idx < data.length; idx++) {
    returnJson[data[idx].name] = data[idx].value
  }
  return returnJson;
}

var escapeHtml = function(s) {
  return s.replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
