export function sendFormData (method, url, data, requestArgs) {
  requestArgs = requestArgs || {};
  var formData = new FormData();
  for (var key of Object.keys(data)) {
    formData.append(key, data[key]);
  }
  requestArgs.data = formData;
  requestArgs.url = api_path + url;
  requestArgs.method = method;
  return $.ajax(requestArgs);
}

export function informUser (message, alertClass) {
  /*
      Show user some information at top of screen.
      alertClass options are 'success', 'info', 'warning', 'danger'
   */
  $('.popup-alert button.close').click();
  alertClass = alertClass || "info";
  $('<div class="alert alert-'+alertClass+' alert-dismissible popup-alert" role="alert" style="display: none">' +
      '<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>'+
      message +
    '</div>').prependTo('body').fadeIn('fast');
}

// via http://www.w3schools.com/js/js_cookies.asp
export function setCookie (cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + "; " + expires;
}



export function getCookie (name) {
  var cookieValue;
  if (document.cookie) {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = $.trim(cookies[i]);
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) == (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

export function csrfSafeMethod (method) {
  // these HTTP methods do not require CSRF protection
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// check if this is a retina-style display
// via http://stackoverflow.com/a/20413768
export function isHighDensity() {
  return (
    (window.matchMedia &&
      (window.matchMedia('only screen and (min-resolution: 124dpi), only screen and (min-resolution: 1.3dppx), only screen and (min-resolution: 48.8dpcm)').matches ||
       window.matchMedia('only screen and (-webkit-min-device-pixel-ratio: 1.3), only screen and (-o-min-device-pixel-ratio: 2.6/2), only screen and (min--moz-device-pixel-ratio: 1.3), only screen and (min-device-pixel-ratio: 1.3)').matches
    )) || (window.devicePixelRatio && window.devicePixelRatio > 1.3));
}

export function getWindowLocationSearch() {
  return window.location.search;
}

export var variables = {
  localStorageKey:"perma_selection"
};

export var jsonLocalStorage = {
  getItem: function (key) {
    var result = localStorage.getItem(key);
    try {
      result = JSON.parse(result);
    } catch (e) {
      result
    }
    return result;
  },
  setItem: function(key, value) {
    if(typeof value !== "string") {
      value = JSON.stringify(value);
    }
    localStorage.setItem(key, value);
  }
}


export function triggerOnWindow(message, data) {
  $(window).trigger(message, data);
}
