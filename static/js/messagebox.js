
// namespace
var MessageBox = MessageBox || {
  ERROR: 0,
  WARN: 1,
  INFO: 2,
  SUCCESS: 3,

  SEVERITY_TEXT: ["error", "warn", "info", "success"],
  CSS_STYLE: ["alert-danger", "alert-warning", "alert-info", "alert-success"]
};

MessageBox.error = function(text) {
  MessageBox._showMessage(text, MessageBox.CSS_STYLE[MessageBox.ERROR]);
};

MessageBox.warn = function(text) {
  MessageBox._showMessage(text, MessageBox.CSS_STYLE[MessageBox.WARN]);
};

MessageBox.info = function(text) {
  MessageBox._showMessage(text, MessageBox.CSS_STYLE[MessageBox.INFO]);
};

MessageBox.success = function(text) {
  MessageBox._showMessage(text, MessageBox.CSS_STYLE[MessageBox.SUCCESS]);
};

MessageBox.registerReadyFunction = function() {
  $(".airone-messagebox").ready(function() {
    var msgs = window.sessionStorage.getItem(['airone-message']);
    if(msgs) {
      for(let msg of JSON.parse(msgs)) {
        switch(Number(msg['code'])) {
        case MessageBox.ERROR:
          MessageBox.error(msg['text']);
          break;
        case MessageBox.WARN:
          MessageBox.warn(msg['text']);
          break;
        case MessageBox.INFO:
          MessageBox.info(msg['text']);
          break;
        case MessageBox.SUCCESS:
          MessageBox.success(msg['text']);
          break;
        }
      }
      window.sessionStorage.removeItem(['airone-message']);
    }
  });
};
MessageBox.registerReadyFunction();

MessageBox.setNextOnLoadMessage = function(code, text){
  // To display multiple messages, set localStorage as Array
  var data = window.sessionStorage.getItem(['airone-message']);
  if(data) {
    data = JSON.parse(data);
    data.push({'code': code.toString(), 'text': text});
    window.sessionStorage.setItem(['airone-message'], JSON.stringify(data));
  } else {
    window.sessionStorage.setItem(['airone-message'], JSON.stringify([{'code': code.toString(), 'text': text}]));
  }
};

MessageBox._showMessage = function(text, style) {
  var content = '<div class="alert alert-dismissible ' + style + ' fade show in" role="alert">'+
    '<button type="button" class="close" data-dismiss="alert" aria-label="close">' +
      '<span aria-hidden="true">&times;</span>' +
    '</button>' +
    '<a id="message">' + text + '</a></div>';
  $(".airone-messagebox").html(content);
  $(".alert").alert();
};

MessageBox.clear = function() {
  $(".airone-messagebox").empty();
};
