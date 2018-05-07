let Handlebars = require('handlebars');

function human_timestamp(datetime) {
    return new Date(datetime).toLocaleString("en-us", {
        year:   "numeric",
        month:  "long",
        day:    "numeric",
        hour:   "numeric",
        minute: "2-digit"
    });
}

module.exports = function(datetime) {
  return Handlebars.escapeExpression(human_timestamp(datetime));
};
