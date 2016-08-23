describe("Test error-handler.js", function() {
  beforeEach(function() {
    airbrake = undefined;
    jasmine.Ajax.install();
    jasmine.Ajax.stubRequest('/manage/errors/resolve').andReturn({
      responseText: 'Issue has been resolved'
    });

    jasmine.Ajax.stubRequest('/errors/new?').andReturn({
      responseText: 'Error has been created'
    });

  });

  afterEach(function() {
    jasmine.Ajax.uninstall();
  });

  it("defines airbrake on init", function(){
    expect(airbrake).not.toBeDefined();
    ErrorHandler.init();
    expect(airbrake).toBeDefined();
  });

  it("pings erorr url on notify", function(){
    ErrorHandler.init();
    var newErrorObject = airbrake.notify("Horrible Mistake", {});
    var request = jasmine.Ajax.requests.mostRecent();
    expect(request.method).toEqual('POST');
    expect(request.params).toBeDefined();
  });

  it("pings resolve url on error resolve request", function(){
    ErrorHandler.init();
    var newErrorObject = airbrake.notify("Horrible Mistake", {});
    ErrorHandler.resolve(1);
    var request = jasmine.Ajax.requests.mostRecent();
    expect(request.method).toEqual('POST');
    expect(request.params).toEqual('error_id=1');
    expect(request.responseText).toEqual('Issue has been resolved');
  });

});
