var LinksListModule = LinksListModule || {};

$(document).ready(function() {
  LinksListModule.init();
  LinksListModule.setupEventHandlers();
  LinksListModule.setupLinksTableEventHandlers();
})

LinksListModule.init = function () {
  this.linkTable = $('.item-rows');
  this.dragStartPosition = null;
  this.lastRowToggleTime = 0;
}

LinksListModule.setupEventHandlers = function () {
  $(window)
    .on("FolderTreeModule.selectionChange", function(evt, data) {
      if (typeof data !== 'object') data = JSON.parse(data);
      LinksListModule.selectedFolderID = data.folderId;
      LinksListModule.showFolderContents(data.folderId);
    });
    // search form
  $('.search-query-form').on('submit', function (e) {
    e.preventDefault();
    var query = DOMHelpers.getValue('.search-query');
    if(query && query.trim()){
      LinksListModule.showFolderContents(LinksListModule.selectedFolderID, query);
    }
  });
}

LinksListModule.getLinkIDForFormElement = function (element) {
  return element.closest('.item-container').find('.item-row').attr('link_id');
}

var saveBufferSeconds = 0.5,
  timeouts = {};
  // save changes in a given text box to the server
LinksListModule.saveInput = function(inputElement, statusElement, name, callback) {
  DOMHelpers.changeHTML(statusElement, 'Saving...');

  var guid = inputElement.attr('id').match(/.+-(.+-.+)/)[1],
    timeoutKey = guid+name;

  if(timeouts[timeoutKey])
    clearTimeout(timeouts[timeoutKey]);

  // use a setTimeout so notes are only saved once every few seconds
  timeouts[timeoutKey] = setTimeout(function () {
    var data = {};
    data[name] = DOMHelpers.getValue(inputElement);
    var request = APIModule.request("PATCH", '/archives/' + guid + '/', data).done(function(data){
      DOMHelpers.changeHTML(statusElement, 'Saved!');
    });
    if (callback) request.done(callback);
  }, saveBufferSeconds*1000);
}
LinksListModule.setupLinksTableEventHandlers = function () {
  LinksListModule.linkTable
    .on('click', 'a.clear-search', function (e) {
      e.preventDefault();
      LinksListModule.showFolderContents(LinksListModule.selectedFolderID);
    })
    .on('mousedown touchstart', '.item-row', function (e) {
      LinksListModule.handleMouseDown(e);
      // .item-row mouseup -- hide and show link details, if not dragging
    })
    .on('mouseup touchend', '.item-row', function (e) {
      LinksListModule.handleMouseUp(e);
    // save changes to notes field
    })
    .on('input propertychange change', '.link-notes', function () {
      var textarea = $(this);
      LinksListModule.saveInput(textarea, textarea.prevAll('.notes-save-status'), 'notes');

    // save changes to title field
    })
    .on('textchange', '.link-title', function () {
      var textarea = $(this);
      LinksListModule.saveInput(textarea, textarea.prevAll('.title-save-status'), 'title', function () {
        // update display title when saved
        textarea.closest('.item-container').find('.item-title span').text(textarea.val());
      });

    // handle move-to-folder dropdown
    })
    .on('change', '.move-to-folder', function () {
      var moveSelect = $(this);
      var data = JSON.stringify({ folderId: moveSelect.val(), linkId: LinksListModule.getLinkIDForFormElement(moveSelect) })
      $(window).trigger("LinksListModule.moveLink", data)
    });
}

// *** actions ***

var showLoadingMessage = false;
LinksListModule.initShowFolderDOM = function (query) {
  if(!query || !query.trim()){
    // clear query after user clicks a folder
    delete query;
    DOMHelpers.setInputValue('.search-query', '');
  }

  // if fetching folder contents takes more than 500ms, show a loading message
  showLoadingMessage = true;
  setTimeout(function(){
    if(showLoadingMessage) {
      DOMHelpers.emptyElement(LinksListModule.linkTable);
      DOMHelpers.changeHTML(LinksListModule.linkTable, '<div class="alert-info">Loading folder contents...</div>');
    }
  }, 500);
}

LinksListModule.generateLinkFields = function(query, link) {
  return LinkHelpers.generateLinkFields(link, query);
};

LinksListModule.showFolderContents = function (folderID, query) {
  this.initShowFolderDOM(query);

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
    APIModule.request("GET", endpoint, requestData).always(function (response) {
        // same thing runs on success or error, since we get back success or error-displaying HTML
      showLoadingMessage = false;
      var links = response.objects.map(LinksListModule.generateLinkFields.bind(this, query));

      // append HTML
      if(requestData.offset === 0) {
        DOMHelpers.emptyElement(LinksListModule.linkTable);
      }
      var linksLoadingMore = LinksListModule.linkTable.find('.links-loading-more');
      DOMHelpers.removeElement(linksLoadingMore);
      LinksListModule.linkTable.append(templates.created_link_items({links: links, query: query}));

      // If we received exactly `requestCount` number of links, there may be more to fetch from the server.
      // Set a waypoint event to trigger when the last link comes into view.
      if(links.length == requestCount){
        requestData.offset += requestCount;
        LinksListModule.linkTable.find('.item-container:last').waypoint(function(direction) {
          this.destroy();  // cancel waypoint
          LinksListModule.linkTable.append('<div class="links-loading-more">Loading more ...</div>');
          getNextContents();
        }, {
          offset:'100%'  // trigger waypoint when element hits bottom of window
        });
      }
    });
  }
  getNextContents();
}

LinksListModule.handleMouseDown = function (e) {
  if ($(e.target).hasClass('no-drag'))
    return;

  $.vakata.dnd.start(e, {
    jstree: true,
    obj: $(e.currentTarget),
    nodes: [
        {id: $(e.currentTarget).attr('link_id')}
    ]
  }, '<div id="jstree-dnd" class="jstree-default"><i class="jstree-icon jstree-er"></i>[link]</div>');

  // record drag start position so we can check how far we were dragged on mouseup
  this.dragStartPosition = [e.pageX || e.originalEvent.touches[0].pageX, e.pageY || e.originalEvent.touches[0].pageY];
}

LinksListModule.handleMouseUp = function (e) {
  // prevent JSTree's tap-to-drag behavior
  $.vakata.dnd.stop(e);

  // don't treat this as a click if the mouse has moved more than 5 pixels -- it's probably an aborted drag'n'drop or touch scroll
  if(this.dragStartPosition && Math.sqrt(Math.pow(e.pageX-this.dragStartPosition[0], 2)*Math.pow(e.pageY-this.dragStartPosition[1], 2))>5)
    return;

  // don't toggle faster than twice a second (in case we get both mouseup and touchend events)
  if(new Date().getTime() - this.lastRowToggleTime < 500)
    return;
  this.lastRowToggleTime = new Date().getTime();

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
    var currentFolderID = this.selectedFolderID,
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
