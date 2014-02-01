var monthLookup = ["Jan.","Feb.","March","April","May","June","July","Aug.","Sept.","Oct.","Nov.","Dec."];
function localDateTime(seconds){
    var d = new Date(seconds*1000 - (new Date().getTimezoneOffset())*60*1000),
        hours = d.getHours(),
        minutes = d.getMinutes(),
        amOrPm = (hours >= 12 ? "p.m" : "a.m");
    hours = hours % 12 || 12;
    return [
        monthLookup[d.getMonth()]+" ",
        d.getDate()+" ",
        d.getFullYear()+", ",
        hours+":",
        (minutes<10?"0":"")+minutes+" ",
        amOrPm
    ].join("");
}