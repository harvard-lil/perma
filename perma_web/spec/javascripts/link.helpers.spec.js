describe("Test link.helpers.js", function() {
  beforeEach(function(){
    expect(LinkHelpers).toBeDefined();
    window.linkObj = {
          captures: [ {
            content_type: "text/html",
            playback_url: "//perma.dev:8000/warc/ZFK8-B42T/http://example.com",
            record_type: "response",
            role: "primary",
            status: "success",
            url:"http://example.com",
            user_upload: false,
          }, {
            content_type:"image/png",
            playback_url:"//perma.dev:8000/warc/ZFK8-B42T/id_/file:///ZFK8-B42T/cap.png",
            record_type:"resource",
            role:"screenshot",
            status:"success",
            url:"file:///ZFK8-B42T/cap.png",
            user_upload:false,
          }, {
            content_type:"favicon",
            playback_url:"//perma.dev:8000/warc/ZFK8-B42T/id_/file:///ZFK8-B42T/favicon.ico",
            record_type:"resource",
            role:"favicon",
            status:"success",
            url:"file:///ZFK8-B42T/favicon.ico",
            user_upload:false,
          }
        ],
          creation_timestamp:"2016-08-18T20:55:18Z",
          creation_timestamp_formatted:"August 18, 2016",
          expiration_date_formatted:"undefined NaN, NaN",
          favicon_url:"",
          guid:"ZFK8-B42T",
          local_url:"localhost:8000/ZFK8-B42T",
          title:"Example Domain",
          url:"http://example.com",
          view_count:1,
          warc_size:21030
      }
  });
  afterEach(function(){
    delete window.linkObj;
  });
  describe("Test findFaviconUrl", function(){
    it("finds favicon url when one exists", function(){
      var url = LinkHelpers.findFaviconURL(window.linkObj);
      expect(url).toEqual("//perma.dev:8000/warc/ZFK8-B42T/id_/file:///ZFK8-B42T/favicon.ico");
    });
    it("does not error when favicon does not exist", function(){
      var linkObjCopy = window.linkObj;
      linkObjCopy.captures = [window.linkObj.captures[0], window.linkObj.captures[1]];
      var url = LinkHelpers.findFaviconURL(linkObjCopy);
      expect(url).toEqual("")
    })
  })
});
