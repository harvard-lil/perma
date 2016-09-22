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
  this.linkRows.click(function(e){
    if (e.target.className == 'clear-search') {
      SearchModule.clearLinks();
      DOMHelpers.setInputValue('.search-query', '');
    }
  });

  this.searchSubmit.submit(function (e) {
    e.preventDefault();
    SearchModule.clearLinks();
    SearchModule.clearCalendar();

    SearchModule
      .getAllLinks()
      .then(function(response){
        var latestDate = SearchModule.formatDate(response.objects[0].creation_timestamp)
        SearchModule.displayCalendar(response.objects);
        SearchModule.getLinksForDate(latestDate);
      });
  });
}

SearchModule.formatDate = function(date) {
  var newDate = new Date(date);
  newDate.setHours(0,0,0,0);
  return '' + (newDate.getMonth() + 1)  + '-'  + newDate.getDate() + '-' + newDate.getFullYear();
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

SearchModule.clearCalendar = function() {
  DOMHelpers.removeClass('#calendar', 'hasDatepicker');
  DOMHelpers.emptyElement('#calendar');
}

SearchModule.displayCalendar = function(links) {
  var dates = {}
  links.map(function(link){
    var newDate = new Date(link.creation_timestamp);
    newDate.setHours(0,0,0,0);
    dates[newDate] = true})

  $('#calendar').datepicker({
    maxDate: "+1d",
    beforeShowDay: function(day) {
      if (dates[day]) {
        return [true, 'active-date']
      } else {return [false]}
    }
  });
}

SearchModule.initCalSearch = function() {
  $('.active-date').click(function(e){
    var el = e.currentTarget;
    var pickedDate = '' + (parseInt(el.dataset.month) + 1)  + '-'  + el.innerText + '-' + el.dataset.year
    SearchModule.getLinksForDate(pickedDate);
  });
}

SearchModule.getAllLinks = function() {
  var query = SearchModule.getQuery();
  var endpoint, request, requestData;
  endpoint = this.getSubmittedUrlEndpoint();
  requestData = {submitted_url:query}
  return APIModule.request("GET", endpoint, requestData).always(function (response) {
    return response.objects;
  });
}

SearchModule.getLinksForDate = function(date) {
  var query = SearchModule.getQuery();
  var endpoint, request, requestData;
  SearchModule.clearLinks();
  endpoint = this.getSubmittedUrlEndpoint();
  requestData = SearchModule.generateRequestData(query, date);
  APIModule.request("GET", endpoint, requestData).always(function (response) {
    var links = response.objects.map(SearchModule.generateLinkFields);
    DOMHelpers.emptyElement(this.linkRows);
    SearchModule.displayLinks(links, query);
    SearchModule.initCalSearch();
  });
}

SearchModule.getSubmittedUrlEndpoint = function () {
  return "/public/archives";
}

SearchModule.generateRequestData = function(query, date) {
  return {submitted_url:query, offset:0, date:date};
}

SearchModule.generateLinkFields = function(link) {
  return LinkHelpers.generateLinkFields(link);
}
