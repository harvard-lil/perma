require('jquery-ui/ui/widgets/datepicker'); // add .datepicker to jquery

var DOMHelpers = require('./helpers/dom.helpers.js');
var HandlebarsHelpers = require('./helpers/handlebars.helpers.js');
var APIModule = require('./helpers/api.module.js');
var LinkHelpers = require('./helpers/link.helpers.js');

var linkRows;
var searchSubmit;
var dates;

function init(){
  linkRows = $('.item-rows');
  searchSubmit = $('.search-query-form');

  setupEventHandlers();
}

function setupEventHandlers() {
  linkRows.click(function(e){
    if (e.target.className == 'clear-search') {
      clearLinks();
      DOMHelpers.setInputValue('.search-query', '');
    }
  });

  searchSubmit.submit(function (e) {
    e.preventDefault();
    clearLinks();
    clearCalendar();

    getAllLinks().then(function(response){
        setDates(response.objects);
        displayCalendar(response.objects);
      });
  });
}

function displayLinks(links, query) {
  var templateId = '#search-links-template';
  var templateArgs = { links: links, query: query };
  var template = HandlebarsHelpers.renderTemplate(templateId, templateArgs);
  linkRows.append(template);
}

function getQuery() {
  var query = DOMHelpers.getValue('.search-query');
  if (!query) return '';
  return query.trim();
}

function clearLinks() {
  DOMHelpers.emptyElement(linkRows);
}

function clearCalendar() {
  DOMHelpers.removeClass('#calendar', 'hasDatepicker');
  DOMHelpers.emptyElement('#calendar');
  DOMHelpers.hideElement('#calendar');
}

function displayCalendar() {

  $('#calendar').datepicker({
    maxDate: "+1d",
    numberOfMonths: 3,
    stepMonths: 3,
    onChangeMonthYear: function(year, minMonth){
      var query = getQuery();
      var endpoint, requestData;
      endpoint = getSubmittedUrlEndpoint();
      minMonth = minMonth < 10 ? '0' + minMonth : minMonth.toString();
      var date =  minMonth + "-01-" + year;
      requestData = generateRequestData(query, date);
      APIModule.request("GET", endpoint, requestData).always(function (response) {
        setDates(response.objects);
        displayCalendar();
        initCalSearch();
      });
    },
    beforeShowDay: function(day) {
      var dates = getDates();
      if (dates[day]) {
        return [true, 'active-date'];
      } else {
        return [false];
      }
    }
  }).datepicker('refresh');
  initCalSearch();
  DOMHelpers.addCSS('#calendar', 'display', 'table');
}

function setDates(links) {
  dates = {};
  if (links) {
    links.map(function(link){
      var newDate = new Date(link.creation_timestamp);
      newDate.setHours(0,0,0,0);
      dates[newDate] = true});
  }
  return dates
}

function getDates(){
  return dates
}

function initCalSearch() {
  $('td')
    .off('click')
    .on('click', function(e){
      if(!$(this).hasClass('active-date')){
        return;
      }
      $('.active-date').removeClass('selected-date');
      $(this).addClass('selected-date');
      var el = e.currentTarget;
      // JS zero-indexes months for some crazy reason, python doesn't. We have to increment it here.
      var pickedDate = '' + (parseInt(el.dataset.month) + 1)  + '-'  + el.innerText + '-' + el.dataset.year
      getLinksForDate(pickedDate);
  });
}

function getAllLinks() {
  var query = getQuery();
  var endpoint, requestData;
  endpoint = getSubmittedUrlEndpoint();
  requestData = generateRequestData(query)
  return APIModule.request("GET", endpoint, requestData);
}

function getLinksForDate(date) {
  var query = getQuery();
  var endpoint, requestData;
  clearLinks();
  endpoint = getSubmittedUrlEndpoint();
  requestData = generateRequestData(query, date);
  delete requestData.date_range;

  APIModule.request("GET", endpoint, requestData).always(function (response) {
    var links = response.objects.map(generateLinkFields);
    DOMHelpers.emptyElement(linkRows);
    displayLinks(links, query);
    initCalSearch();
  });
}

function getSubmittedUrlEndpoint () {
  return "/public/archives";
}

function generateRequestData(query, date) {
  var data = { submitted_url:query, offset:0, date_range:3, limit:0};
  if (date) {
    date = new Date(date);
    date = date.toISOString();
    data.date = date
  }
  return data;
}

function generateLinkFields(link) {
  return LinkHelpers.generateLinkFields(link);
}

init();