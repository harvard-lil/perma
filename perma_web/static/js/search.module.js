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
  this.searchSubmit.on('submit', function (e) {
    e.preventDefault();
    var query = SearchModule.getQuery();
    SearchModule.getLinks(query);
  });
}

SearchModule.displayLinks = function(links, query) {
  this.linkRows.append(templates.search_links({ links: links, query: query }));
}

SearchModule.getQuery = function() {
  var query = DOMHelpers.getValue('.search-query');
  if (!query) return '';
  return query.trim();
}

SearchModule.getLinks = function(query) {
  var endpoint, request, requestData;
  endpoint = this.getSubmittedUrlEndpoint();
  requestData = SearchModule.generateRequestData(query);
  request = Helpers.apiRequest("GET", endpoint, requestData);
  // Content fetcher.
  // This is wrapped in a function so it can be called repeatedly for infinite scrolling.
  function getNextContents() {
    request.always(function (response) {
        // same thing runs on success or error, since we get back success or error-displaying HTML
      showLoadingMessage = false;
      var links = response.objects.map(SearchModule.generateLinkFields);
      console.log("links:", links);
      if(requestData.offset === 0) { DOMHelpers.emptyElement(this.linkRows); }

      DOMHelpers.removeElement(SearchModule.linkRows.find('.links-loading-more'));
      SearchModule.displayLinks(links, query);

      // If we received exactly `requestData.limit` number of links, there may be more to fetch from the server.
      // Set a waypoint event to trigger when the last link comes into view.
      if(links.length == requestData.limit){
        requestData.offset += requestData.limit;
        this.linkRows.find('.item-container:last').waypoint(function(direction) {
          this.destroy();  // cancel waypoint
          this.linkRows.append('<div class="links-loading-more">Loading more ...</div>');
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
