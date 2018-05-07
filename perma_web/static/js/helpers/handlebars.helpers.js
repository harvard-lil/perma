var Handlebars = require('handlebars');

/*
Using handlebar's compile method to generate templates on the fly
*/

var templateCache = {};
export function renderTemplate(templateId, args) {
  args = args || {};
  let $this = $(templateId);
  if (!templateCache[templateId]) {
    templateCache[templateId] = Handlebars.compile($this.html());
  }
  return templateCache[templateId](args);
}

/* simple wrapper around Handlebars.compile() to cache the compiled templates */
export function compileTemplate(templateId) {
  var $this = $(templateId);
  if ($this.length) {
    var template = Handlebars.compile($this.html());
    templateCache[templateId] = template;
    return template;
  }
}
