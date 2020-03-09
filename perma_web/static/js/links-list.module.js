require('waypoints/lib/jquery.waypoints.js');  // add .waypoint to jquery

var DOMHelpers = require('./helpers/dom.helpers.js');
var LinkHelpers = require('./helpers/link.helpers.js');
var APIModule = require('./helpers/api.module.js');
var FolderSelectorHelper = require('./helpers/folder-selector.helper.js');

// templates
let headerTemplate = require("./hbs/link-list-header.handlebars");
let linkTemplate = require("./hbs/link.handlebars");

let dragStartPosition = null;
let lastRowToggleTime = 0;
let selectedFolderID = null;

// elements in the DOM, retrieved during init()
let $linkListHeader, $linkTable;

export function init () {
  $linkTable = $('.item-rows');
  $linkListHeader = $('#link-list-header');

  setupEventHandlers();
  setupLinksTableEventHandlers();
}

function setupEventHandlers () {
  $(window)
    .on("FolderTreeModule.selectionChange", function(evt, data) {
      if (typeof data !== 'object') data = JSON.parse(data);
      selectedFolderID = data.folderId;
      showFolderContents(data.folderId);
      let template = headerTemplate({
        "organization": data.orgId,
        "path": data.path.join(" > "),
        "folder": data.folderId
      });
      $linkListHeader.html(template);
    })
    .on("BatchLinkModule.batchCreated", function(){
      showFolderContents(selectedFolderID);
    })
    .on("BatchLinkModule.refreshLinkList", function(){
      showFolderContents(selectedFolderID);
    });

  // search form
  $('.search-query-form').on('submit', function (e) {
    e.preventDefault();
    let query = DOMHelpers.getValue('.search-query');
    if(query && query.trim()){
      showFolderContents(selectedFolderID, query);
    }
  });

  // scroll helper
  DOMHelpers.markIfScrolled('.col-links');
}

function getLinkIDForFormElement (element) {
  return element.closest('.item-container').find('.item-row').data('link_id');
}

function setupLinksTableEventHandlers () {
  $linkTable
    .on('click', 'a.clear-search', function (e) {
      e.preventDefault();
      showFolderContents(selectedFolderID);
    })
    .on('mousedown touchstart', '.item-row', function (e) {
      handleMouseDown(e);
    })

    // .item-row mouseup -- hide and show link details, if not dragging
    .on('mouseup touchend', '.item-row', function (e) {
      handleMouseUp(e);
    })

    // save changes to notes field
    .on('input propertychange change', '.link-notes', function () {
      let textarea = $(this);
      let guid = getLinkIDForFormElement(textarea);
      LinkHelpers.saveInput(guid, textarea, textarea.prevAll('.notes-save-status'), 'notes');
    })

    // save changes to title field
    .on('input', '.link-title', function () {
      let textarea = $(this);
      let guid = getLinkIDForFormElement(textarea);
      LinkHelpers.saveInput(guid, textarea, textarea.prevAll('.title-save-status'), 'title', function (data) {
        // update display title when saved
        textarea.closest('.item-container').find('.item-title span').text(data.title);
      });
    })

    .on('input', '.link-description', function () {
      let textarea = $(this);
      let guid = getLinkIDForFormElement(textarea);
      LinkHelpers.saveInput(guid, textarea, textarea.prevAll('.description-save-status'), 'description')
    })

    // handle move-to-folder dropdown
    .on('change', '.move-to-folder', function () {
      let moveSelect = $(this);
      let data = JSON.stringify({ folderId: moveSelect.val(), linkId: getLinkIDForFormElement(moveSelect) })
      $(window).trigger("LinksListModule.moveLink", data)
    });
}

// *** actions ***

let showLoadingMessage = false;
function initShowFolderDOM (query) {
  if(!query || !query.trim()){
    // clear query after user clicks a folder
    DOMHelpers.setInputValue('.search-query', '');
  }

  // if fetching folder contents takes more than 500ms, show a loading message
  showLoadingMessage = true;
  setTimeout(function(){
    if(showLoadingMessage) {
      DOMHelpers.emptyElement($linkTable);
      DOMHelpers.changeHTML($linkTable, '<div class="alert-info">Loading folder contents...</div>');
    }
  }, 500);
}

function generateLinkFields(query, link) {
  return LinkHelpers.generateLinkFields(link, query);
}

function showFolderContents (folderID, query) {
  initShowFolderDOM(query);

  let requestCount = 20,
    requestData = {limit: requestCount, offset:0},
    endpoint;

  if (query) {
    requestData.q = query;
  }
  endpoint = '/folders/' + folderID + '/archives/';

  // Content fetcher.
  // This is wrapped in a function so it can be called repeatedly for infinite scrolling.
  function getNextContents() {
    APIModule.request("GET", endpoint, requestData)
        .done(function (response) {
          showLoadingMessage = false;
          let links = response.objects.map(generateLinkFields.bind(this, query));

          // append HTML
          if(requestData.offset === 0) {
            // first run -- initialize folder
            DOMHelpers.emptyElement($linkTable);
          } else {
            // subsequent run -- appending to folder
            let linksLoadingMore = $linkTable.find('.links-loading-more');
            DOMHelpers.removeElement(linksLoadingMore);
            if(!links.length)
              return;
          }

        displayLinks(links, query);
        // Ensure footer can be reached
        DOMHelpers.scrollIfTallerThanFractionOfViewport(".col-links", 0.9);

        // If we received exactly `requestCount` number of links, there may be more to fetch from the server.
        // Set a waypoint event to trigger when the last link comes into view.
        if(links.length === requestCount){
          requestData.offset += requestCount;
          $linkTable.find('.item-container:last').waypoint(function(direction) {
            if (direction == 'down'){
              this.destroy();  // cancel waypoint
              $linkTable.append('<div class="links-loading-more">Loading more ...</div>');
              getNextContents();
            }
          }, {
            offset:'100%',  // trigger waypoint when element hits bottom of window,
            context: '.col-links'
          });
        }
    });
  }
  getNextContents();
}

function displayLinks(links, query) {
  let template = linkTemplate({links: links, query: query});
  $linkTable.append(template);
  $('.toggle-details, .item-row._isDraggable').click(function(e){
    e.stopPropagation();
    toggleLinkDetails(e);
  });
}

function handleMouseDown (e) {
  if ($(e.target).hasClass('no-drag'))
    return;

  $.vakata.dnd.start(e, {
    jstree: true,
    obj: $(e.currentTarget),
    nodes: [
        {id: $(e.currentTarget).data('link_id')}
    ]
  }, '<div id="jstree-dnd" class="jstree-default"><i class="jstree-icon jstree-er"></i>[link]</div>');

  // record drag start position so we can check how far we were dragged on mouseup
  dragStartPosition = [e.pageX || e.originalEvent.touches[0].pageX, e.pageY || e.originalEvent.touches[0].pageY];
}

function handleMouseUp (e) {
  // prevent JSTree's tap-to-drag behavior
  $.vakata.dnd.stop(e);

  // don't treat this as a click if the mouse has moved more than 5 pixels -- it's probably an aborted drag'n'drop or touch scroll
  if(dragStartPosition && Math.sqrt(Math.pow(e.pageX-dragStartPosition[0], 2)*Math.pow(e.pageY-dragStartPosition[1], 2))>5)
    return;

  // don't toggle faster than twice a second (in case we get both mouseup and touchend events)
  if(new Date().getTime() - lastRowToggleTime < 500)
    return;
  lastRowToggleTime = new Date().getTime();
}

let getLinkContainer = function(elem) {
  return $(elem).closest('.item-container');
};

let toggleLinkDetails = function(e) {
  if (e.target.tagName == 'A' && e.target.classList.contains('no-drag')) {
    // Don't toggle details if the user has clicked on the Perma Link URL,
    // the original URL, or the delete button
    return
  }

  let linkContainer = getLinkContainer(e.target),
      details = linkContainer.find('.item-details');
  if (details.is(':visible')) {
    hideLinkDetails(linkContainer, details);
  } else {
    showLinkDetails(linkContainer, details);
  }
};

let hideLinkDetails = function (linkContainer, details) {
  linkContainer.find('.collapse-details').blur().hide();
  linkContainer.find('.expand-details').show().focus();
  details.hide();
  linkContainer.toggleClass( '_active' );
};

let showLinkDetails = function (linkContainer, details) {
  // when showing link details, update the move-to-folder select input
  // based on the current folderTree structure

  // first clear the select ...
  let currentFolderID = selectedFolderID,
    moveSelect = details.find('.move-to-folder');
  FolderSelectorHelper.makeFolderSelector(moveSelect, currentFolderID);
  details.show();
  linkContainer.toggleClass('_active');
  linkContainer.find('.expand-details').blur().hide();
  linkContainer.find('.collapse-details').show().focus();
};
