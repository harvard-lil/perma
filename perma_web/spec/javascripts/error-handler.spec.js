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
});
