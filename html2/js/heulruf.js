
function test(){
$.get( "data/", function( data ) {
  var html = $.parseHTML( data );
  // Iterate all links in the document received that end on
  // .mp3, parse these URLs and make them into a playlist
  // by splitting them into the name, date, etc part.
  var links = $("a[href$='mp3']", html);
  var tracklist = {};

  for (i=0; i<links.length; i++){
  	var loc = links[i].getAttribute("href");
	var parts = loc.split(/[-.]/);
	if (parts.length == 3) {
		var timestamp;
		timestamp = Date(parseInt(parts[1]))
		
	}
  }
  alert( "Load was performed." );
});
}

// Initializer
$(document).ready(function() {

	$("#test").on("click", test);

});
