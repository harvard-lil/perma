var Handlebars = require('handlebars');
var HandlebarsHelpers = require('./handlebars.helpers.js');
var template;

function register_progress_bar(){
    template = HandlebarsHelpers.compileTemplate('#progress-bar-template');
    if (template) {
        Handlebars.registerPartial('progressBar', template);
    }
}
register_progress_bar();

var progress_bars_by_id = {};

/* Creates a new "progress bar," which renders as such and exposes a simple API for setting progress */
export function make_progress_bar(id) {
    if (!template){
        register_progress_bar();
    }
    var $container = $("<div>").html(template({'progress': 0, 'id': id}));

    var obj = {
        setProgress: function(progress) {
            $container.empty();
            $container.html(template({'progress': progress, 'id': id}));
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
