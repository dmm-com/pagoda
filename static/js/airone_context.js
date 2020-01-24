
// namespace
var AirOneContext = AirOneContext || {
  _previousContext: {}
};

AirOneContext.getPreviousContext = function() {
  return AirOneContext._previousContext;
};

AirOneContext.getPreviousItem = function(key) {
  return AirOneContext._previousContext[key];
};
// shorthand 
AirOneContext.get = AirOneContext.getPreviousItem;

AirOneContext.onReady = function() {
  let prev_str = window.localStorage.getItem('airone-context');
  if(prev_str != null) {
    AirOneContext._previousContext = JSON.parse(prev_str);
  }

  AirOneContext.setCurrentContext({
    'URL': window.location.href
  });
};
$(window).ready(AirOneContext.onReady);

AirOneContext.getCurrentContext = function() {
  let curr_str = window.localStorage.getItem('airone-context');
  if(curr_str != null) {
    return JSON.parse(curr_str);
  } else {
    return {};
  };
};

AirOneContext.setCurrentContext = function(data) {
  window.localStorage.setItem('airone-context', JSON.stringify(data));
};

AirOneContext.addCurrentItem = function(key, value) {
  let curr = AirOneContext.getCurrentContext();
  curr[key] = value;
  window.localStorage.setItem('airone-context', JSON.stringify(curr));
};
// shorthand 
AirOneContext.add = AirOneContext.addCurrentItem;
