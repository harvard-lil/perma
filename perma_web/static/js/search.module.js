var SearchModule = SearchModule || {};
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
    var query, url, request;
    query = $('.search-query').val();
    if(query && query.trim()){
      url = "/public/archives?submitted_url=" + query;
      request = Helpers.apiRequest("GET", url);
      request.done(function(data) {
        SearchModule.display_links(data.objects, query);
      });
    }
  });
}


SearchModule.display_links = function(links, query) {
  this.linkRows.append(templates.search_links({links: links, query: query}));
}
