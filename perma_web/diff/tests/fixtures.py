example_html_str = """
<!DOCTYPE html>
<html><head>
    <title>Example Domain</title>

    <meta charset="utf-8">
    <meta http-equiv="Content-type" content="text/html; charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style type="text/css">
    div {
        width: 600px;
        margin: 5em auto;
        padding: 50px;
        background-color: #fff;
        border-radius: 1em;
    }
    a:link, a:visited {
        color: #38488f;
        text-decoration: none;
    }
    </style>
</head>

<body>
<div>
    <h1>Example Domain</h1>
    <p>This domain is established to be used for illustrative examples in documents. You may use this
    domain in examples without prior coordination or asking for permission.</p>
    <p><a href="http://www.iana.org/domains/example">More information...</a></p>
</div>
</body><script>someFunctionCall(); console.log("uh oh!")</script></html>
"""

example_diff_html_str = """
<!DOCTYPE html>
<html><head></head>

<body>
<div>
    <h1>Example Domain</h1>
    <p>This domain is established to be used for illustrative examples in documents. You may use this
    domain in examples without prior coordination or asking for permission.</p>
    <p><a href="http://www.iana.org/domains/example">More information...</a></p>
</div>
</body><script>someFunctionCall(); console.log("uh oh!")</script></html>
"""

unminified_script = """function asdf(some_arg) {
  if (some_arg){
    console.log("hello!");
  }
}"""

minified_script = 'function asdf(a){a&&console.log("hello!")}'

unminified_script2 = """angular.module('pd', ['ui.router', 'angularFileUpload'])
.config(function($stateProvider, $urlRouterProvider){
  $urlRouterProvider.otherwise("/");

  $stateProvider
    .state('upload', {
      url: '',
      controller: 'upload',
      templateUrl: 'features/upload/partial.html',
    })

})

.controller('upload', function($scope, $http, $timeout, $upload, getFileTypes){
  $scope.browseOrUpload   = 'browse';
  $scope.extensions       = [];
  $scope.formats          = getFileTypes.all;
  $scope.extensionsPicked = '  ';

  $scope.showName         = function(ext, val, mouse) {
    if(mouse){
      // document.getElementById(ext).innerText = val
    } else {
      document.getElementById(ext).innerText = ext;
    }
  }

  $scope.chooseExtension = function(format) {
    var indexOfExtension = $scope.extensions.indexOf(format);
    if(indexOfExtension < 0){
      $scope.extensions.push(format);
      document.getElementById(format).style.backgroundColor = '#FF9290';
    } else {
      $scope.extensions.splice(indexOfExtension, 1);
      document.getElementById(format).style.backgroundColor = '#E5E5E5';
    }
    if($scope.extensions.length) {
      $scope.extensionsPicked = 'convert to: '+$scope.extensions.join(' + ');
    } else {
      $scope.extensionsPicked = ' ';
    }
  };


  $scope.onFileSelect = function($files) {
    $scope.upload = [];
    $scope.uploadResult = [];
    $scope.selectedFiles = $files;
    $scope.dataUrls = [];
    var singlefileIdx = 0;
    var $file = $files[singlefileIdx];

    var fileReader = new FileReader();
    fileReader.readAsDataURL($files[singlefileIdx]);

    fileReader.onload = function(e) {
      $timeout(function() {
        $scope.dataUrls[singlefileIdx] = e.target.result;

        $scope.browseOrUpload = 'upload';
        $scope.filename = $file.name;
      });
    }
  };

  $scope.start = function(index) {
    $scope.errorMsg = null;
    $scope.upload[index] = $upload.upload({
      url : 'upload',
      method: 'POST',
      data : {
        extensions : JSON.stringify($scope.extensions),
      },
      file: $scope.selectedFiles[index],
    }).then(function(response) {
      console.log('success!', response);
      $scope.uploadResult.push(response.data);
    }, function(response) {
      console.log('error!');
      if (response.status > 0) $scope.errorMsg = response.status + ': ' + response.data;
    })
  };

  $scope.abort = function(index) {
    $scope.upload[index] = null;
    $scope.browseOrUpload = 'browse';
    $scope.filename = '';
  };

})

.service('postFile', function($http, $timeout, $upload) {
  return {
    upload: function(file, extensions) {
      var formData = new FormData();
      formData.append('file', file);
      formData.append('extensions', extensions);
      $http({
        method: 'POST',
        url: '/upload',
        data: formData,
        headers: {'Content-Type': undefined},
        transformRequest: angular.identity
      }).success(function(data) {
        console.log('success!')
      }).error(function(data){
        console.error('error!',data)
      });
    }
  };
})

.service('getFileTypes', function(){
  return {
    all: {
      'json': "JSON",
      'html': "HyperText Markup Language",
      'html5': "HyperText Markup Language 5",
      'xhtml': "extensible HyperText Markup Language",
      'rst': "reStructuredText",
      'asciidoc': "AsciiDoc",
      'context': "ConTeXt",
      'docbook': "DocBook",
      'docx': "Word docx",
      'dzslides': "DZSlides HTML5 + javascript slide show",
      'epub': "EPUB v2 book",
      'epub3': "EPUB v3",
      'fb2': "FictionBook2 e-book",
      'html': "HyperText Markup Language",
      'html5': "HyperText Markup Language 5",
      'icml': "InDesign ICML",
      'json': "JSON",
      'latex': "LaTex",
      'man': "groff man",
      'markdown': "Extended Markdown",
      'mediawiki': "MediaWiki markup",
      'native': "Native Haskell",
      'odt': "OpenOffice text document",
      'opendocument': "OpenDocument",
      'opml': "OPML",
      'org': "Emacs Org-Mode",
      'plain': "plain text",
      'revealjs': "reveal.js HTML5 + javascript slide show",
      'rst': "reStructuredText",
      'rtf': "rich text format",
      's5': "S5 HTML and javascript slide show",
      'slidy': "Slideous HTML and javascript slide show",
      'texinfo': "GNU Texinfo",
      'textile': "Textile"
    }
  }
});"""


unminified_css = """//  Locally hosted Google Fonts

@font-face {
  font-family: "Roboto Slab";
  font-style: normal;
  font-weight: 300;
  src: url('../fonts/RobotoSlab-Light.eot');
  src: local("Roboto Slab Light"), local("RobotoSlab-Light"), url('../fonts/RobotoSlab-Light.eot?#iefix') format("embedded-opentype"), url('../fonts/RobotoSlab-Light.woff') format("woff"), url('../fonts/RobotoSlab-Light.ttf') format("truetype");
}

@font-face {
  font-family: "Roboto Slab";
  font-style: normal;
  font-weight: 400;
  src: url('../fonts/RobotoSlab-Regular.eot');
  src: local("Roboto Slab Regular"), local("RobotoSlab-Regular"), url('../fonts/RobotoSlab-Regular.eot?#iefix') format("embedded-opentype"), url('../fonts/RobotoSlab-Regular.woff') format("woff"), url('../fonts/RobotoSlab-Regular.ttf') format("truetype");
}

@font-face {
  font-family: "Roboto";
  font-style: normal;
  font-weight: 300;
  src: url('../fonts/Roboto-Light-webfont.eot');
  src: local("Roboto Light"), local("Roboto-Light"), url('../fonts/Roboto-Light-webfont.eot?#iefix') format("embedded-opentype"), url('../fonts/Roboto-Light-webfont.woff') format("woff"), url('../fonts/Roboto-Light-webfont.ttf') format("truetype");
}

@font-face {
  font-family: "Roboto";
  font-style: normal;
  font-weight: 400;
  src: url('../fonts/Roboto-Regular-webfont.eot');
  src: local("Roboto Regular"), local("Roboto-Regular"), url('../fonts/Roboto-Regular-webfont.eot?#iefix') format("embedded-opentype"), url('../fonts/Roboto-Regular-webfont.woff') format("woff"), url('../fonts/Roboto-Regular-webfont.ttf') format("truetype");
}

@font-face {
  font-family: "Roboto";
  font-style: normal;
  font-weight: 700;
  src: url('../fonts/Roboto-Bold-webfont.eot');
  src: local("Roboto Bold"), local("Roboto-Bold"), url('../fonts/Roboto-Bold-webfont.eot?#iefix') format("embedded-opentype"), url('../fonts/Roboto-Bold-webfont.woff') format("woff"), url('../fonts/Roboto-Bold-webfont.ttf') format("truetype");
}

@font-face {
  font-family: "Roboto";
  font-style: normal;
  font-weight: 900;
  src: url('../fonts/Roboto-Black-webfont.eot');
  src: local("Roboto Black"), local("Roboto-Black"), url('../fonts/Roboto-Black-webfont.eot?#iefix') format("embedded-opentype"), url('../fonts/Roboto-Black-webfont.woff') format("woff"), url('../fonts/Roboto-Black-webfont.ttf') format("truetype");
}

/*
@font-face {
  font-family: "Inconsolata";
  font-style: normal;
  font-weight: 400;
  src: url('../fonts/RobotoSlab-Regular.eot');
  src: local("Roboto Slab Regular"), local("RobotoSlab-Regular"), url('../fonts/RobotoSlab-Regular.eot?#iefix') format("embedded-opentype"), url('../fonts/RobotoSlab-Regular.woff') format("woff"), url('../fonts/RobotoSlab-Regular.ttf') format("truetype");
}
*/"""

minified_script2 = """angular.module("pd",["ui.router","angularFileUpload"]).config(function(e,o){o.otherwise("/"),e.state("upload",{url:"",controller:"upload",templateUrl:"features/upload/partial.html"})}).controller("upload",function(e,o,t,n,a){e.browseOrUpload="browse",e.extensions=[],e.formats=a.all,e.extensionsPicked="  ",e.showName=function(e,o,t){t||(document.getElementById(e).innerText=e)},e.chooseExtension=function(o){var t=e.extensions.indexOf(o);0>t?(e.extensions.push(o),document.getElementById(o).style.backgroundColor="#FF9290"):(e.extensions.splice(t,1),document.getElementById(o).style.backgroundColor="#E5E5E5"),e.extensions.length?e.extensionsPicked="convert to: "+e.extensions.join(" + "):e.extensionsPicked=" "},e.onFileSelect=function(o){e.upload=[],e.uploadResult=[],e.selectedFiles=o,e.dataUrls=[];var n=0,a=o[n],s=new FileReader;s.readAsDataURL(o[n]),s.onload=function(o){t(function(){e.dataUrls[n]=o.target.result,e.browseOrUpload="upload",e.filename=a.name})}},e.start=function(o){e.errorMsg=null,e.upload[o]=n.upload({url:"upload",method:"POST",data:{extensions:JSON.stringify(e.extensions)},file:e.selectedFiles[o]}).then(function(o){console.log("success!",o),e.uploadResult.push(o.data)},function(o){console.log("error!"),o.status>0&&(e.errorMsg=o.status+": "+o.data)})},e.abort=function(o){e.upload[o]=null,e.browseOrUpload="browse",e.filename=""}}).service("postFile",function(e,o,t){return{upload:function(o,t){var n=new FormData;n.append("file",o),n.append("extensions",t),e({method:"POST",url:"/upload",data:n,headers:{"Content-Type":void 0},transformRequest:angular.identity}).success(function(e){console.log("success!")}).error(function(e){console.error("error!",e)})}}}).service("getFileTypes",function(){return{all:{json:"JSON",html:"HyperText Markup Language",html5:"HyperText Markup Language 5",xhtml:"extensible HyperText Markup Language",rst:"reStructuredText",asciidoc:"AsciiDoc",context:"ConTeXt",docbook:"DocBook",docx:"Word docx",dzslides:"DZSlides HTML5 + javascript slide show",epub:"EPUB v2 book",epub3:"EPUB v3",fb2:"FictionBook2 e-book",html:"HyperText Markup Language",html5:"HyperText Markup Language 5",icml:"InDesign ICML",json:"JSON",latex:"LaTex",man:"groff man",markdown:"Extended Markdown",mediawiki:"MediaWiki markup","native":"Native Haskell",odt:"OpenOffice text document",opendocument:"OpenDocument",opml:"OPML",org:"Emacs Org-Mode",plain:"plain text",revealjs:"reveal.js HTML5 + javascript slide show",rst:"reStructuredText",rtf:"rich text format",s5:"S5 HTML and javascript slide show",slidy:"Slideous HTML and javascript slide show",texinfo:"GNU Texinfo",textile:"Textile"}}});"""

minified_css = """// Locally hosted Google Fonts @font-face{font-family:"Roboto Slab";font-style:normal;font-weight:300;src:url(../fonts/RobotoSlab-Light.eot);src:local("Roboto Slab Light"),local("RobotoSlab-Light"),url('../fonts/RobotoSlab-Light.eot?#iefix') format("embedded-opentype"),url(../fonts/RobotoSlab-Light.woff) format("woff"),url(../fonts/RobotoSlab-Light.ttf) format("truetype")}@font-face{font-family:"Roboto Slab";font-style:normal;font-weight:400;src:url(../fonts/RobotoSlab-Regular.eot);src:local("Roboto Slab Regular"),local("RobotoSlab-Regular"),url('../fonts/RobotoSlab-Regular.eot?#iefix') format("embedded-opentype"),url(../fonts/RobotoSlab-Regular.woff) format("woff"),url(../fonts/RobotoSlab-Regular.ttf) format("truetype")}@font-face{font-family:"Roboto";font-style:normal;font-weight:300;src:url(../fonts/Roboto-Light-webfont.eot);src:local("Roboto Light"),local("Roboto-Light"),url('../fonts/Roboto-Light-webfont.eot?#iefix') format("embedded-opentype"),url(../fonts/Roboto-Light-webfont.woff) format("woff"),url(../fonts/Roboto-Light-webfont.ttf) format("truetype")}@font-face{font-family:"Roboto";font-style:normal;font-weight:400;src:url(../fonts/Roboto-Regular-webfont.eot);src:local("Roboto Regular"),local("Roboto-Regular"),url('../fonts/Roboto-Regular-webfont.eot?#iefix') format("embedded-opentype"),url(../fonts/Roboto-Regular-webfont.woff) format("woff"),url(../fonts/Roboto-Regular-webfont.ttf) format("truetype")}@font-face{font-family:"Roboto";font-style:normal;font-weight:700;src:url(../fonts/Roboto-Bold-webfont.eot);src:local("Roboto Bold"),local("Roboto-Bold"),url('../fonts/Roboto-Bold-webfont.eot?#iefix') format("embedded-opentype"),url(../fonts/Roboto-Bold-webfont.woff) format("woff"),url(../fonts/Roboto-Bold-webfont.ttf) format("truetype")}@font-face{font-family:"Roboto";font-style:normal;font-weight:900;src:url(../fonts/Roboto-Black-webfont.eot);src:local("Roboto Black"),local("Roboto-Black"),url('../fonts/Roboto-Black-webfont.eot?#iefix') format("embedded-opentype"),url(../fonts/Roboto-Black-webfont.woff) format("woff"),url(../fonts/Roboto-Black-webfont.ttf) format("truetype")}"""
