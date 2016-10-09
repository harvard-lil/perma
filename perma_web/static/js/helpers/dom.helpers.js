export function setInputValue(domSelector, value) {
  $(domSelector).val(value);
}

export function removeElement(domSelector) {
  $(domSelector).remove();
}

export function changeText(domSelector, text) {
  $(domSelector).text(text);
}

export function toggleBtnDisable(domSelector, disableStatus) {
  // if disableStatus is false, enable.
  // if disableStatus is true, disable.
  $(domSelector).prop('disabled', disableStatus);
}

export function changeHTML(domSelector, value) {
  $(domSelector).html(value);
}

export function emptyElement(domSelector) {
  $(domSelector).empty();
}

export function getValue (domSelector) {
  return $(domSelector).val();
}

export function removeClass (domSelector, className) {
  $(domSelector).removeClass(className);
}

export function showElement (domSelector) {
  $(domSelector).show();
}

export function hideElement (domSelector) {
  $(domSelector).hide();
}

export function addCSS (domSelector, propertyName, propertyValue) {
  $(domSelector).css(propertyName, propertyValue);
}
