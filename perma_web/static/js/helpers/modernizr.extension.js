if(Modernizr){
  Modernizr.addTest('FormData', function(){
    return window.FormData !== undefined;
  });
}
