var send_export_request = function(format) {
  MessageBox.clear();

  $.ajax({
    url: `/entry/export/{{ entity.id }}?format=${ format }`,
    type: 'GET',
    dataType: 'json',
    contentType: 'application/x-www-form-urlencoded;charset=utf-8',
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
var send_export_request_yaml = function(e) {
  send_export_request('YAML');
}
var send_export_request_csv = function(e) {
  send_export_request('CSV');
}

