var Handlebars = require('handlebars');
var HandlebarsHelpers = require('./handlebars.helpers.js');

var template = HandlebarsHelpers.compileTemplate('#progress-bar-template')
if (template) {
    Handlebars.registerPartial('progressBar', template);
}

var progress_bars_by_id = {};

/* Creates a new "progress bar," which renders as such and exposes a simple API for setting progress */
export function make_progress_bar(id) {
    let template = template || HandlebarsHelpers.compileTemplate('#progress-bar-template');
    var $container = $("<div>").html(template(0, id));

    var obj = {
        setProgress: function(progress) {
            $container.empty();
            $container.html(template(progress, id));
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
