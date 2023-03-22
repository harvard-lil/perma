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


setInterval(function(){ fillSection("celery_queues")}, 2000);

function refresh_celery_jobs(){
  return setInterval(function(){ fillSection("celery")}, 2000);
}
let celery_tasks_refresh = null;
document.getElementById('toggle-tasks-auto-refresh').addEventListener('click', (e) => {
  if (celery_tasks_refresh){
    clearInterval(celery_tasks_refresh);
    celery_tasks_refresh = null;
    e.target.innerText = 'Start Auto-Refresh (every 2s)';
  } else {
    celery_tasks_refresh = refresh_celery_jobs();
    e.target.innerText = 'Stop Auto-Refresh';
  }
})


function refresh_rate_limits(){
  let status = document.getElementById('rate-limits-status')
  status.innerText = 'Refreshing...';
  fillSection("rate_limits", () => {
    status.innerText = 'Refreshed!';
    setTimeout(()=> status.innerText = '', 2000);
  });
}
function auto_refresh_rate_limits(){
  return setInterval(function(){ refresh_rate_limits()}, 15000);
}
document.getElementById('refresh-rate-limits').addEventListener('click', (e) => {
  refresh_rate_limits()
})
let rate_limits_refresh = null;
document.getElementById('auto-refresh-rate-limits').addEventListener('click', (e) => {
  if (rate_limits_refresh){
    clearInterval(rate_limits_refresh);
    rate_limits_refresh = null;
    e.target.innerText = 'Start Auto-Refresh (every 15s)';
  } else {
    e.target.innerText = 'Stop Auto-Refresh';
    refresh_rate_limits()
    rate_limits_refresh = auto_refresh_rate_limits();
  }
})


function refresh_capture_jobs(){
  return setInterval(function(){ fillSection("job_queue")}, 2000);
}
let capture_jobs_refresh = null;
document.getElementById('toggle-capture-jobs-auto-refresh').addEventListener('click', (e) => {
  if (capture_jobs_refresh){
    clearInterval(capture_jobs_refresh);
    capture_jobs_refresh = null;
    e.target.innerText = 'Start Auto-Refresh (every 2s)';
  } else {
    capture_jobs_refresh = refresh_capture_jobs();
    e.target.innerText = 'Stop Auto-Refresh';
  }
})
