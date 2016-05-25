describe("Test error-handler.js", function() {
  beforeEach(function() {
    airbrake = undefined;
    jasmine.Ajax.install();
  });

  afterEach(function() {
    jasmine.Ajax.uninstall();
  });

  it("defines airbrake on init", function(){
    expect(airbrake).not.toBeDefined();
    ErrorHandler.init();
    expect(airbrake).toBeDefined();
  });

  xit("triggers airbrake on error on window error", function(){
    ErrorHandler.init();
    expect(airbrake).toBeDefined();
    spyOn(airbrake, "onerror");
    try {
      throw "Deliberate Error!";
    } catch (e) {
      expect(airbrake.onerror).toHaveBeenCalled();
    }
  });
  xit("resolves error if it exist", function(){
    ErrorHandler.init();
    var newErrorObject = airbrake.notify("Horrible Mistake", {});
    var result = ErrorHandler.resolve(1);
  })
});
