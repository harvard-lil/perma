window.SearchModule = window.SearchModule || {};
$(document).ready(function (){
  SearchModule.init();
  SearchModule.setupEventHandlers();
});

SearchModule.init = function(){
  this.linkRows = $('.item-rows');
  this.searchSubmit = $('.search-query-form');
}

SearchModule.setupEventHandlers = function() {
  this.linkRows.on('click', function(e){
    if (e.target.className == 'clear-search') {
      SearchModule.clearLinks();
      DOMHelpers.setInputValue('.search-query', '');
    }
  });

  this.searchSubmit.on('submit', function (e) {
    e.preventDefault();
    var query = SearchModule.getQuery();
    SearchModule.getLinks(query);
  });
}

SearchModule.displayLinks = function(links, query) {
  var templateId = '#search-links-template';
  var templateArgs = { links: links, query: query };
  var template = HandlebarsHelpers.renderTemplate(templateId, templateArgs);
  this.linkRows.append(template);
}

SearchModule.getQuery = function() {
  var query = DOMHelpers.getValue('.search-query');
  if (!query) return '';
  return query.trim();
}

SearchModule.clearLinks = function() {
  DOMHelpers.emptyElement(this.linkRows);
}

SearchModule.getLinks = function(query) {
  var endpoint, request, requestData;
  SearchModule.clearLinks();
  endpoint = this.getSubmittedUrlEndpoint();
  requestData = SearchModule.generateRequestData(query);

  // Content fetcher.
  // This is wrapped in a function so it can be called repeatedly for infinite scrolling.
  function getNextContents() {
    APIModule.request("GET", endpoint, requestData).always(function (response) {
      // same thing runs on success or error, since we get back success or error-displaying HTML
      var links = response.objects.map(SearchModule.generateLinkFields);
      if(requestData.offset === 0) { DOMHelpers.emptyElement(this.linkRows); }

      DOMHelpers.removeElement(SearchModule.linkRows.find('.links-loading-more'));
      SearchModule.displayLinks(links, query);

      // If we received exactly `requestData.limit` number of links, there may be more to fetch from the server.
      // Set a waypoint event to trigger when the last link comes into view.
      if(links.length == requestData.limit){
        requestData.offset += requestData.limit;
        SearchModule.linkRows.find('.item-container:last')
          .waypoint(function(direction) {
            this.destroy();  // cancel waypoint
            SearchModule.linkRows.append('<div class="links-loading-more">Loading more ...</div>');
            getNextContents();
          }, {
            offset:'100%'  // trigger waypoint when element hits bottom of window
          });
      }
    });
  }
  getNextContents();
}

SearchModule.getSubmittedUrlEndpoint = function () {
  return "/public/archives";
}

SearchModule.generateRequestData = function(query) {
  return {submitted_url:query, limit: 20, offset:0}
}

SearchModule.generateLinkFields = function(link) {
  return LinkHelpers.generateLinkFields(link);
}
