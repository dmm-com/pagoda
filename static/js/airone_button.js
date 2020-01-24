
/*
AirOne Button Component

add wrapper to a button 
- disable the button, change text, and run the registered function when clicked
- re-enable the button and change text again when the function finished 

Usage:
put button in HTML
    <input type="button" class="btn btn-primary" id="submit-button" value="save" />

initialize like below:
    AirOneButtonUtil.initialize($("#submit-button"), "save", "saving...", true, false, function(){
        // do something
    });

Functions:
AirOneButtonUtil.initialize(button, enabled_text, disabled_text, is_enabled, is_async, on_click_handler)
    button:           jQuery object for the button. (e.g. $("#submit-button"))
    enabled_text:     text when the button is clickable (e.g. "save")
    disabled_text:    text when the button is running `on_click_handler` (e.g. "saving...")
    is_enabled:       true if the button is clickable after initialized
    is_async:         true if `on_click_handler` performs async process such as ajax
                      if true, user must re-enable the button in `on_click_handler`
    on_click_handler: main function when the button is clicked 
*/

// namespace
var AirOneButtonUtil = AirOneButtonUtil || {};

AirOneButtonUtil.initialize = function(button, enabled_text, disabled_text, is_enabled, is_async, on_click_handler) {
  // register custom attr
  button.attr('enabled-text', enabled_text);
  button.attr('disabled-text', disabled_text);
  button.attr('is-async', is_async);

  // register custom event listener
  button.on('enableButton', function() {
    button.prop('disabled', false);
    button.prop('value', button.attr('enabled-text'));
  });

  button.on('disableButton', function() {
    button.prop('disabled', true);
    button.prop('value', button.attr('disabled-text'));
  });

  // register custom event
  button.on('click', function(e) {
    button.trigger('disableButton');
    on_click_handler(e);
    if(!button.attr('is-async')) {
      button.trigger('enableButton');
    };
  });
  
  // initialize state
  if(is_enabled) {
    button.trigger('enableButton');
  } else {
    button.trigger('disableButton');
  };
};
