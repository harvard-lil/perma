$(document).ready(function() {
    $("#details-button").click(function () {
        $(this).text($(this).text() == "Show record details" ? "Hide record details" : "Show record details");
        $('header').toggleClass('_activeDetails');
    });    

    adjustHeight();
    $('#collapse-refresh').on('shown.bs.collapse', function () {
        adjustHeight();
    });
    $('#collapse-refresh').on('hidden.bs.collapse', function () {
        adjustHeight();
    });

	function adjustHeight() {
	    var	headerHeight = $('header').height(),
	    	windowHeight = $(window).height();
	    $('iframe').height(windowHeight - headerHeight - 0);
	}
});