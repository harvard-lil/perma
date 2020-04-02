let Handlebars = require('handlebars');

function _human_timestamp (datetime) {
    return new Date(datetime).toLocaleString("en-us", {
        year:   "numeric",
        month:  "long",
        day:    "numeric",
        hour:   "numeric",
        minute: "2-digit"
    });
}

export default function human_timestamp (datetime) {
  return Handlebars.escapeExpression(_human_timestamp(datetime));
};
