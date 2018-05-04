let progressBarTemplate = require("../hbs/progress-bar.handlebars");

var progress_bars_by_id = {};

/* Creates a new "progress bar," which renders as such and exposes a simple API for setting progress */
export function make_progress_bar(id) {
  let initial = progressBarTemplate({'progress': 0, 'id': id});
  let $container = $("<div>").html(initial);
  let obj = {
    setProgress: function(progress) {
      $container.empty();
      let template = progressBarTemplate({
        'progress': progress,
        'id': id
      });
      $container.html(template);
    },
    appendTo: function($el) {
      $container.appendTo($el);
    }
  };
  progress_bars_by_id[id] = obj;
  return obj;
}

export function get_progress_bar_by_id(id) {
  return progress_bars_by_id[id];
}
