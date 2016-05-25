var localStorage;
var current_user;

describe("Test create.module.js", function() {
  beforeEach(function(){
    localStorage = {
      setItem: function (key, val) {
        this[key] = JSON.stringify(val);
      getItem: function (key) { return this[key]; }
    }
    spyOn(localStorage, 'getItem').andReturn JSON.stringify({ 1: {"folderId":27,"orgId":1}})
  });
  afterEach(function() {
    localStorage = {}
  });


  it("defines CreateModule", function(){
    expect(CreateModule).toBeDefined();
  });
  describe("localStorage methods", function(){
    it("defines ls", function(){
      expect(ls).toBeDefined();
    });
  });
});
