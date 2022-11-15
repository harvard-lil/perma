var DOMHelpers = require('./helpers/dom.helpers.js');
var HandlebarsHelpers = require('./helpers/handlebars.helpers.js');

function fillSection(name){
  $.getJSON(document.location.href.replace(/\/$/, "") + "/" + name).then(function (data) {
    if (name == 'celery' && (!data.queues || !Boolean(data.queues.length))){
      // If no data was returned, don't redraw the section.
      return
    }
    DOMHelpers.changeHTML('#' + name, HandlebarsHelpers.renderTemplate('#' + name + '-template', data));
  });
}

fillSection("job_queue");
fillSection("celery_queues");
fillSection("celery");
fillSection("days");
fillSection("random");
fillSection("emails");

setInterval(function(){ fillSection("job_queue")}, 2000);
setInterval(function(){ fillSection("celery_queues")}, 2000);
setInterval(function(){ fillSection("celery")}, 2000);
