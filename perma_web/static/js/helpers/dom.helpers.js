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

export function scrollIfTallerThanFractionOfViewport(domSelector, fraction){
  let limit = fraction * viewportHeight();
  let elem = $(domSelector);
  if(elem.prop('scrollHeight') < limit){
    elem.removeClass('scrolling');
    elem.css('max-height', 'initial');
  } else {
    elem.addClass('scrolling');
    elem.css('max-height', limit);
  }
}

export function viewportHeight(){
  return Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
}

export function markIfScrolled(domSelector){
  let elem = $(domSelector);
  elem.scroll(function(){
    if (hasScrolled(elem)){
      elem.addClass('scrolled');
    } else {
      elem.removeClass('scrolled');
    }
  })
}

function hasScrolled(elem){
  return elem.children().first().position().top < 0;
}
