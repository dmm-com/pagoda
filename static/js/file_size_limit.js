// Check the limit of file size when import
var upfile = $('#upfile')[0];

if(upfile){
  upfile.addEventListener("change", function(evt){
    var str = "";
    var file = evt.target.files[0];

    // Inform when file size over the limit
    if( file.size >= LIMIT_FILE_SIZE ){
      str += LIMIT_PHRASE + "<br>";
      str += "ファイル名：" + file.name + "<br>";
      str += "ファイルサイズ：" + file.size + "byte<br>";
      MessageBox.error(str);
      $('#send').prop('disabled', true);  // disable submit
    } else {
      $('#send').prop('disabled', false); // enable submit
    }
  },false);
}
