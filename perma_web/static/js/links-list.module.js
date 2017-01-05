require('waypoints/lib/jquery.waypoints.js');  // add .waypoint to jquery

var DOMHelpers = require('./helpers/dom.helpers.js');
var LinkHelpers = require('./helpers/link.helpers.js');
var HandlebarsHelpers = require('./helpers/handlebars.helpers.js');
var APIModule = require('./helpers/api.module.js');

var FolderTreeModule = require('./folder-tree.module.js');


var linkTable = null;
var dragStartPosition = null;
var lastRowToggleTime = 0;
var selectedFolderID = null;

export function init () {
  linkTable = $('.item-rows');
  setupEventHandlers();
  setupLinksTableEventHandlers();
}

function setupEventHandlers () {
  $(window)
    .on("FolderTreeModule.selectionChange", function(evt, data) {
      if (typeof data !== 'object') data = JSON.parse(data);
      selectedFolderID = data.folderId;
      showFolderContents(data.folderId);
    });
    // search form
  $('.search-query-form').on('submit', function (e) {
    e.preventDefault();
    var query = DOMHelpers.getValue('.search-query');
    if(query && query.trim()){
      showFolderContents(selectedFolderID, query);
    }
  });
}

function getLinkIDForFormElement (element) {
  return element.closest('.item-container').find('.item-row').data('link_id');
}

function setupLinksTableEventHandlers () {
  linkTable
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
      var textarea = $(this);
      var guid = getLinkIDForFormElement(textarea);
      LinkHelpers.saveInput(guid, textarea, textarea.prevAll('.notes-save-status'), 'notes');
    })

    // save changes to title field
    .on('input', '.link-title', function () {
      var textarea = $(this);
      var guid = getLinkIDForFormElement(textarea);
      LinkHelpers.saveInput(guid, textarea, textarea.prevAll('.title-save-status'), 'title', function (data) {
        // update display title when saved
        textarea.closest('.item-container').find('.item-title span').text(data.title);
      });
    })

    // handle move-to-folder dropdown
    .on('change', '.move-to-folder', function () {
      var moveSelect = $(this);
      var data = JSON.stringify({ folderId: moveSelect.val(), linkId: getLinkIDForFormElement(moveSelect) })
      $(window).trigger("LinksListModule.moveLink", data)
    });
}

// *** actions ***

var showLoadingMessage = false;
function initShowFolderDOM (query) {
  if(!query || !query.trim()){
    // clear query after user clicks a folder
    DOMHelpers.setInputValue('.search-query', '');
  }

  // if fetching folder contents takes more than 500ms, show a loading message
  showLoadingMessage = true;
  setTimeout(function(){
    if(showLoadingMessage) {
      DOMHelpers.emptyElement(linkTable);
      DOMHelpers.changeHTML(linkTable, '<div class="alert-info">Loading folder contents...</div>');
    }
  }, 500);
}

function generateLinkFields(query, link) {
  return LinkHelpers.generateLinkFields(link, query);
};

function showFolderContents (folderID, query) {
  initShowFolderDOM(query);

  var requestCount = 20,
    requestData = {limit: requestCount, offset:0},
    endpoint;

  if (query) {
    requestData.q = query;
    endpoint = '/archives/';
  } else {
    endpoint = '/folders/' + folderID + '/archives/';
  }
  // Content fetcher.
  // This is wrapped in a function so it can be called repeatedly for infinite scrolling.
  function getNextContents() {
    APIModule.request("GET", endpoint, requestData).success(function (response) {
      showLoadingMessage = false;
      var links = response.objects.map(generateLinkFields.bind(this, query));

      // append HTML
      if(requestData.offset === 0) {
        // first run -- initialize folder
        DOMHelpers.emptyElement(linkTable);
      }else{
        // subsequent run -- appending to folder
        var linksLoadingMore = linkTable.find('.links-loading-more');
        DOMHelpers.removeElement(linksLoadingMore);
        if(!links.length)
          return;
      }

      displayLinks(links, query);

      // If we received exactly `requestCount` number of links, there may be more to fetch from the server.
      // Set a waypoint event to trigger when the last link comes into view.
      if(links.length == requestCount){
        requestData.offset += requestCount;
        linkTable.find('.item-container:last').waypoint(function(direction) {
          this.destroy();  // cancel waypoint
          linkTable.append('<div class="links-loading-more">Loading more ...</div>');
          getNextContents();
        }, {
          offset:'100%'  // trigger waypoint when element hits bottom of window
        });
      }
    });
  }
  getNextContents();
}

function displayLinks(links, query) {
  var templateId = '#created-link-items-template';
  var templateArgs = {links: links, query: query};
  var template = HandlebarsHelpers.renderTemplate(templateId, templateArgs);
  linkTable.append(template);
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

  // hide/show link details
  var linkContainer = $(e.target).closest('.item-container'),
    details = linkContainer.find('.item-details');

  if (details.is(':visible')) {
    details.hide();
    linkContainer.toggleClass( '_active' )

  } else {
    // when showing link details, update the move-to-folder select input
    // based on the current folderTree structure

    // first clear the select ...
    var currentFolderID = selectedFolderID,
      moveSelect = details.find('.move-to-folder');
    moveSelect.find('option').remove();

    // recursively populate select ...
    function addChildren(node, depth) {
      for (var i = 0; i < node.children.length; i++) {
        var childNode = FolderTreeModule.folderTree.get_node(node.children[i]);

        // For each node, we create an <option> using text() for the folder name,
        // and then prepend some &nbsp; to show the tree structure using html().
        // Using html for the whole thing would be an XSS risk.
        moveSelect.append(
          $("<option/>", {
            value: childNode.data.folder_id,
            text: childNode.text.trim(),
            selected: childNode.data.folder_id == currentFolderID
          }).prepend(
            new Array(depth).join('&nbsp;&nbsp;') + '- '
          )
        );

        // recurse
        if (childNode.children && childNode.children.length)
          addChildren(childNode, depth + 1);
      }
    }
    addChildren(FolderTreeModule.folderTree.get_node('#'), 1);

    details.show();
    linkContainer.toggleClass('_active')
  }
}
