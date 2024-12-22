// ==UserScript==
// @name         Set Wikiwand settings
// @version      2023-08-24
// @description  Set some useful Wikiwand settings, even if the cookies were cleared.
// @match        https://www.wikiwand.com/*
// @run-at       document-start
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/wikiwand_settings.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/wikiwand_settings.user.js
// @grant        none
// ==/UserScript==

(function() {
    window.localStorage.setItem("settings", JSON.stringify({
		theme: "auto",
		fontSize: 3,
		fontFamily: "sans",
		justify: false,
		cover: false,
		shrinkTOC: false,
		linksColor: true,
		references: true,
		openAI: false,
		readyToRender: true,
		articleWidth: 10,
	}));
	window.addEventListener("DOMContentLoaded", function() {
		var el = document.createElement("style");
		el.textContent = `
    [class^=navbar_install], [class^=navbar_icons]:nth-of-type(2) li:first-child {
        display:none;
	}
    .wiki-thumb, .wiki-thumb img {
        width:unset !important;
        min-width:unset !important;
        max-width:unset !important;
    }
    .wiki-thumb {
	    display:table;
		border-collapse:collapse;
		line-height:0;
	}
    .wiki-thumb > a {
	    display:block;
	}
	.wiki-thumb figcaption {
	    display:table-caption;
		caption-side:bottom;
		line-height:1.3em;
	}
	footer {
	    display:none;
    }
	.content-root {
	    margin-bottom:0;
	}
    `;
		document.head.appendChild(el);
	});
})();
