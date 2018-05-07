var DOMHelpers = require('../../static/js/helpers/dom.helpers');
var Helpers = require('../../static/js/helpers/general.helpers');
var CreateLinkModule = require('../../static/js/create-link.module');
var localStorage;
var current_user;


describe("Test create-link.module.js", function() {
  it("defines CreateLinkModule", function(){
    expect(CreateLinkModule).toBeDefined();
  });
  // describe("populateFromUrl", function(){
  //   beforeEach(function(){
  //     spyOn(DOMHelpers, "setInputValue");
  //   });
  //   it("returns the correct url when one exists", function(){
  //     var intendedUrl = "http://research.uni.edu";
  //     spyOn(Helpers, "getWindowLocationSearch").and.returnValue("?url="+intendedUrl);
  //     var url = CreateLinkModule.populateFromUrl();
  //     expect(url).toEqual(intendedUrl);
  //     expect(DOMHelpers.setInputValue).toHaveBeenCalled();
  //   });
  //   it("returns nothing when url does not exist", function(){
  //     spyOn(Helpers, "getWindowLocationSearch").and.returnValue("");
  //     var url = CreateLinkModule.populateFromUrl();
  //     expect(url).not.toBeDefined();
  //     expect(DOMHelpers.setInputValue).not.toHaveBeenCalled();
  //   });
  // });
  describe("updateLinksRemaining", function(){
    it("changes links_remaining", function(){
      spyOn(DOMHelpers, "changeText");
      window.links_remaining = 10;
      CreateLinkModule.updateLinksRemaining(8);
      expect(window.links_remaining).toEqual(8);
      expect(DOMHelpers.changeText).toHaveBeenCalledWith('.links-remaining', 8);
    });
  });
  describe("handleSelectionChange", function(){
    it("is called on event broadcast", function(){
      spyOn(CreateLinkModule, "handleSelectionChange", function(){
        Helpers.triggerOnWindow("FolderTreeModule.selectionChange");
        expect(CreateLinkModule.handleSelectionChange).toHaveBeenCalled();
      });
    });
  });
});
