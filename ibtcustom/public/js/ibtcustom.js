frappe.pages['modules'].on_page_load = function() {
	$("div").remove(".module-section-column:contains('Help')");
}

$(document).load(function(){
	$("div").remove(".module-section-column:contains('Help')");
	$("div .h4").addClass('test');
	
});

$('a.module-link').click(function(){
	$("div").remove(".module-section-column:contains('Help')");
	
});

$(document).ready(function() { 
	$("div .h4").addClass('test');
});


/*$(window).on("load", function() { 
	$("div").remove(".module-section-column:contains('Help')");
});

$(document).bind("load", function() { 
	$("div").remove(".module-section-column:contains('Help')");
});

window.onload = function() {
	$("div").remove(".module-section-column:contains('Help')");
}*/