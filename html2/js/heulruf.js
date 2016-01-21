
function test(){
$.get( "data/", function( data ) {
  var html = $.parseHTML( data );
  // Iterate all links in the document received that end on
  // .mp3, parse these URLs and make them into a playlist
  // by splitting them into the name, date, etc part.
  var links = $("a[href$='mp3']", html);
  var tracklist = [];

  for (i=0; i<links.length; i++){
  	var loc = links[i].getAttribute("href");
	var parts = loc.split(/[-.]/);
	if (parts.length == 3) {
		var timestamp;
		var playlist_element = {};
		timestamp = Date(parseInt(parts[1]))
		playlist_element['title'] = timestamp;
		playlist_element['mp3'] = loc;
		tracklist.push(playlist_element);
	}
  }

  var myPlaylist = new jPlayerPlaylist({
		jPlayer: "#jquery_jplayer_1",
		cssSelectorAncestor: "#jp_container_1"
	}, tracklist
	, {
		swfPath: "../../dist/jplayer",
		supplied: "oga, mp3",
		wmode: "window",
		useStateClassSkin: true,
		autoBlur: false,
		smoothPlayBar: true,
		keyEnabled: true
	});
  alert( "Load was performed." );
});
}

// Initializer
$(document).ready(function() {

	$("#test").on("click", test);

});
