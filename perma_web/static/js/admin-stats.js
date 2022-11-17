var DOMHelpers = require('./helpers/dom.helpers.js');
var HandlebarsHelpers = require('./helpers/handlebars.helpers.js');

function fillSection(name, callback){
  $.getJSON(document.location.href.replace(/\/$/, "") + "/" + name).then(function (data) {
    if (name == 'celery' && (!data.queues || !Boolean(data.queues.length))){
      // If no data was returned, don't redraw the section.
      return
    }
    DOMHelpers.changeHTML('#' + name, HandlebarsHelpers.renderTemplate('#' + name + '-template', data));

    if (callback){
      callback();
    }
  });
}

fillSection("celery_queues");
fillSection("celery");
fillSection("rate_limits");
fillSection("job_queue");
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

document.getElementById('refresh-rate-limits').addEventListener('click', (e) => {
  let status = document.getElementById('rate-limits-status')
  status.innerText = 'Refreshing...';
  fillSection("rate_limits", () => {
    status.innerText = 'Refreshed!';
    setTimeout(()=> status.innerText = '', 2000);
  });
})
