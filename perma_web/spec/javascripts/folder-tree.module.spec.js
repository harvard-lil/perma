// require('jstree');  // add jquery support for .tree
// require('core-js/fn/array/find');
// require('jstree-css/default/style.min.css');
//
// var APIModule = require('../../static/js/helpers/api.module');
var Helpers = require('../../static/js/helpers/general.helpers');
var FolderTreeModule = require('../../static/js/folder-tree.module');
var CreateLinkModule = require('../../static/js/create.module');
var localStorageKey = Helpers.variables.localStorageKey;
var allowedEventsCount = 0;
var lastSelectedFolder = null;
var localStorage;
export var folderTree = null;
// CreateLinkModule.setupEventHandlers();

describe("Test folder-tree.module.js", function() {
  it("defines FolderTreeModule", function(){
    expect(FolderTreeModule).toBeDefined();
  });

  describe("localStorage", function(){
    /* ls related methods */
    it("defines ls", function(){
      expect(FolderTreeModule.ls).toBeDefined();
    });

    describe("getAll", function(){
      it("returns set folders on getAll", function(){
        var setFolders = {1:{"folderIds":[27], "orgId":4}};
        spyOn(Helpers.jsonLocalStorage, "getItem").and.returnValue(setFolders);
        var folders = FolderTreeModule.ls.getAll();
        expect(folders).toEqual(setFolders);
        expect(Helpers.jsonLocalStorage.getItem).toHaveBeenCalled();
      });
      it("returns empty object if nothing is set", function(){
        spyOn(Helpers.jsonLocalStorage, "getItem").and.returnValue("");
        var folders = FolderTreeModule.ls.getAll();
        expect(folders).toEqual({});
      });
    });

    describe("getCurrent", function(){
      it("returns current user folder settings when they exist", function(){
        window.current_user = {id:1};
        var setFolders = {1:{"folderIds":[27], "orgId":4}};
        spyOn(Helpers.jsonLocalStorage, "getItem").and.returnValue(setFolders);
        var folders = FolderTreeModule.ls.getCurrent();
        expect(folders).toEqual(setFolders[1]);
        expect(Helpers.jsonLocalStorage.getItem).toHaveBeenCalled();
      });
      it("returns empty object when current user settings don't exist", function(){
        window.current_user = {id:1};
        var setFolders = {2:{"folderIds":[27], "orgId":4}};
        spyOn(Helpers.jsonLocalStorage, "getItem").and.returnValue(setFolders);
        var folders = FolderTreeModule.ls.getCurrent();
        expect(folders).toEqual({});
        expect(Helpers.jsonLocalStorage.getItem).toHaveBeenCalled();
      });
    });

    describe("setCurrent", function(){
      beforeEach(function(){
        spyOn(Helpers, "triggerOnWindow");
        window.current_user = {id:1};
        spyOn(CreateLinkModule, "updateLinker");
        spyOn(Helpers.jsonLocalStorage, "setItem");
      });
      afterEach(function(){
        delete window.current_user;
      });
      it("sets current user folderId and orgId when they exist", function(){
        var orgId = 2, folderId = 37;
        FolderTreeModule.ls.setCurrent(orgId, [folderId]);
        expect(Helpers.jsonLocalStorage.setItem).toHaveBeenCalledWith("perma_selection",{1:{"folderIds":[folderId],"orgId":orgId}});
      });
      it("sets current user folderId to default if none is provided", function(){
        var orgId = 2;
        FolderTreeModule.ls.setCurrent(orgId);
        expect(Helpers.jsonLocalStorage.setItem).toHaveBeenCalledWith("perma_selection",{1:{"folderIds":undefined,"orgId":orgId}});
        expect(Helpers.triggerOnWindow).toHaveBeenCalled()
      });
    });
  })
});
