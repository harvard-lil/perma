// From https://github.com/harvard-lil/accessibility-tools/blob/master/code/modals/

// For this library to work:
// All non-modal content should be enclosed in a div id="after-modals"

let $modals;
let $focusOnClose;

export function returnFocusTo(elem){
  $focusOnClose = elem;
}

function setup_handlers() {

  // add aria-hidden to all non-modal content, when the modal is open
  $modals.on('show.bs.modal', function (e) {
    $('#after-modals').attr('aria-hidden', true);
  })
  $modals.on('hide.bs.modal', function (e) {
    $('#after-modals').attr('aria-hidden', false);
  })
  $modals.on('hidden.bs.modal', function (e) {
    $focusOnClose.focus();
    $focusOnClose = null;
  })
}

export function init() {
  $(function() {
    $modals = $('.modal');
    setup_handlers();
  });
}

