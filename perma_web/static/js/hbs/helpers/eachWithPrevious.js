let Handlebars = require('handlebars');

module.exports = function(context, options) {
  let data;
  if (options.data) {
    data = Handlebars.createFrame(options.data);
  }
  let rendered = "";
  context.forEach(function(item, index, array){
      data.previous = array[index -1];
      rendered  = rendered + options.fn(item, {data: data})
  });
  return rendered;
}
