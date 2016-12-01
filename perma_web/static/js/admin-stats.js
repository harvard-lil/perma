var DOMHelpers = require('./helpers/dom.helpers.js');
var HandlebarsHelpers = require('./helpers/handlebars.helpers.js');

function fillSection(name){
  return $.getJSON(document.location.href.replace(/\/$/, "") + "/" + name).then(function (data) {
    DOMHelpers.changeHTML('#' + name, HandlebarsHelpers.renderTemplate('#' + name + '-template', data));
  });
}

function addSection(name){
  $('.stats-container').append('<div class="row" id="'+name+'">Loading '+name+' ...</div>');
  return function() { fillSection(name) };
}

var chain = $.when(addSection("random")());
chain = chain.then(addSection("days"));
chain = chain.then(addSection("emails"));
chain = chain.then(addSection("job_queue"));
chain = chain.then(addSection("celery"));

setInterval(function(){ fillSection("job_queue")}, 2000);
