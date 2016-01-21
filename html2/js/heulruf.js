
function load_playlist(){
var data_dir = "./data/"
$.get( data_dir, function( data ) {
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
		timestamp = parseInt(parts[1])
		playlist_element['title'] = new Date(timestamp);
		playlist_element['mp3'] = data_dir+loc;
		playlist_element['unixdate'] = timestamp;
		tracklist.push(playlist_element);
	}
  }
  // Now sort the playlist by unixdate
  tracklist.sort(function(a, b) {
    return a['unixdate'] - b['unixdate'];
    });

  var myPlaylist = new jPlayerPlaylist({
		jPlayer: "#jquery_jplayer_1",
		cssSelectorAncestor: "#jp_container_1"
	}, tracklist
	, {
		swfPath: "bower_components/jPlayer/dist/jplayer/",
		supplied: "oga, mp3",
		wmode: "window",
		useStateClassSkin: true,
		autoBlur: false,
		smoothPlayBar: true,
		keyEnabled: true
	});
});
}

// Initializer
$(document).ready(function() {
	load_playlist();
});
