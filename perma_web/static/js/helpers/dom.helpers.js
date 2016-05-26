DOMHelpers = {}

DOMHelpers.setInputValue = function(domSelector, value) {
  $(domSelector).val(value);
}

DOMHelpers.removeElement = function(domSelector) {
  $(domSelector).remove();
}
