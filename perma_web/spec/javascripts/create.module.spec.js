var localStorage;
var current_user;

describe("Test create.module.js", function() {
  beforeEach(function(){
    localStorage = {
      setItem: function (key, val) { this[key] = val; },
      getItem: function (key) { return this[key]; }
    }
  });
  it("defines CreateModule", function(){
    expect(CreateModule).toBeDefined();
  });

  describe("populateWithUrl", function(){
    beforeEach(function(){
      spyOn(DOMHelpers, "setInputValue");
    });
    it("returns the correct url when one exists", function(){
      var intendedUrl = "http://research.uni.edu";
      spyOn(Helpers, "getWindowLocationSearch").and.returnValue("?url="+intendedUrl);
      var url = CreateModule.populateWithUrl();
      expect(url).toEqual(intendedUrl);
      expect(DOMHelpers.setInputValue).toHaveBeenCalled();
    });
    it("returns nothing when url does not exist", function(){
      spyOn(Helpers, "getWindowLocationSearch").and.returnValue("");
      var url = CreateModule.populateWithUrl();
      expect(url).not.toBeDefined();
      expect(DOMHelpers.setInputValue).not.toHaveBeenCalled();

    })
  });
  describe("localStorage", function(){
    /* ls related methods */
    it("defines ls", function(){
      expect(CreateModule.ls).toBeDefined();
    });
    describe("getAll", function(){
      it("returns set folders on getAll", function(){
        var setFolders = {1:{"folderId":27, "orgId":4}};
        spyOn(Helpers.localStorage, "getItem").and.returnValue(setFolders);
        var folders = CreateModule.ls.getAll();
        expect(folders).toEqual(setFolders);
        expect(Helpers.localStorage.getItem).toHaveBeenCalled();
      });
      it("returns empty object if nothing is set", function(){
        spyOn(Helpers.localStorage, "getItem").and.returnValue("");
        var folders = CreateModule.ls.getAll();
        expect(folders).toEqual({});
      });
    });

    describe("getCurrent", function(){
      it("returns current user folder settings when they exist", function(){
        window.current_user = {id:1};
        var setFolders = {1:{"folderId":27, "orgId":4}};
        spyOn(Helpers.localStorage, "getItem").and.returnValue(setFolders);
        var folders = CreateModule.ls.getCurrent();
        expect(folders).toEqual(setFolders[1]);
        expect(Helpers.localStorage.getItem).toHaveBeenCalled();
      });
      it("returns empty object when current user settings don't exist", function(){
        window.current_user = {id:1};
        var setFolders = {2:{"folderId":27, "orgId":4}};
        spyOn(Helpers.localStorage, "getItem").and.returnValue(setFolders);
        var folders = CreateModule.ls.getCurrent();
        expect(folders).toEqual({});
        expect(Helpers.localStorage.getItem).toHaveBeenCalled();
      });
    });
    describe("setCurrent", function(){
      beforeEach(function(){
        spyOn(Helpers, "triggerOnWindow");
        window.current_user = {id:1};
        spyOn(CreateModule, "updateLinker");
        spyOn(Helpers.localStorage, "setItem");
      });
      afterEach(function(){
        delete window.current_user;
      });
      it("sets current user folderId and orgId when they exist", function(){
        var orgId = 2, folderId = 37;

        CreateModule.ls.setCurrent(orgId, folderId);
        expect(Helpers.localStorage.setItem).toHaveBeenCalledWith("perma_selection",{1:{"folderId":folderId,"orgId":orgId}});
        expect(CreateModule.updateLinker).toHaveBeenCalled();
        expect(Helpers.triggerOnWindow).toHaveBeenCalledWith("dropdown.selectionChange");
      });
      it("sets current user folderId to default if none is provided", function(){
        var orgId = 2;
        CreateModule.ls.setCurrent(orgId);
        expect(Helpers.localStorage.setItem).toHaveBeenCalledWith("perma_selection",{1:{"folderId":"default","orgId":orgId}});
        expect(CreateModule.updateLinker).toHaveBeenCalled();
        expect(Helpers.triggerOnWindow).toHaveBeenCalledWith("dropdown.selectionChange");
      });
    });
  });
});
