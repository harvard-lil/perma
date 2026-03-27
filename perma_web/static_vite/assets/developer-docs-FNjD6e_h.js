function u(r){return typeof r=="object"?r===null?"null":r.constructor==new Array().constructor?"array":r.constructor==new Date().constructor?"date":r.constructor==new RegExp().constructor?"regex":"object":typeof r}function i(r,e){if(arguments.length<2)var e="";var c="    ",o=u(r);if(o=="array"){if(r.length==0)return"[]";var t="["}else{var n=0;if($.each(r,function(){n++}),n==0)return"{}";var t="{"}var n=0;return $.each(r,function(f,a){switch(n>0&&(t+=","),o=="array"?t+=`
`+e+c:t+=`
`+e+c+'"'+f+'": ',u(a)){case"array":case"object":t+=i(a,e+c);break;case"boolean":case"number":t+=a.toString();break;case"null":t+="null";break;case"string":t+='"'+a+'"';break;default:t+="TYPEOF: "+typeof a}n++}),o=="array"?t+=`
`+e+"]":t+=`
`+e+"}",t}$(document).ready(function(){$(".prettyprint").each(function(){try{var r=JSON.parse($(this).text());$(this).html(i(r))}catch{}})});
//# sourceMappingURL=developer-docs-FNjD6e_h.js.map
