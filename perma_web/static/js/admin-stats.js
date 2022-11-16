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

fillSection("celery_queues");
fillSection("job_queue");
fillSection("celery");
fillSection("days");
fillSection("random");
fillSection("emails");

setInterval(function(){ fillSection("job_queue")}, 2000);
setInterval(function(){ fillSection("celery_queues")}, 2000);

function refresh_celery_jobs(){
  return setInterval(function(){ fillSection("celery")}, 2000);
}
let celery_tasks_refresh = refresh_celery_jobs()

document.getElementById('cancel-auto-refresh').addEventListener('click', (e) => {
  if (celery_tasks_refresh){
    clearInterval(celery_tasks_refresh);
    celery_tasks_refresh = null;
    e.target.innerText = 'Resume Auto-Refresh';
  } else {
    celery_tasks_refresh = refresh_celery_jobs();
    e.target.innerText = 'Pause Auto-Refresh';
  }
})
