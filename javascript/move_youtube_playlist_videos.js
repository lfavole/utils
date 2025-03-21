var menuOpen = false;
var counter = 0;
var intv = setInterval(() => {
	if(counter > 0) {
		counter -= 1;
		return;
	}
	var element;
    if(menuOpen) {
		element = $("ytd-menu-service-item-renderer:nth-of-type(5)");
	} else {
		element = $$("ytd-playlist-video-renderer ytd-menu-renderer button").pop();
	}
	if(element) {
		element.click();
		if(menuOpen)
			counter = 10;
		menuOpen = !menuOpen;
	}
}, 500);
