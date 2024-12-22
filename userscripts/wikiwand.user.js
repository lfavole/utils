// ==UserScript==
// @name         Wikiwand
// @description  Like the Wikiwand extension, but cheaper.
// @author       Laurent FAVOLE
// @match        https://*.wikipedia.org/wiki/*
// @run-at       document-start
// @version      2024-08-23
// @icon         https://www.google.com/s2/favicons?sz=64&domain=wikiwand.com
// @grant        GM_addElement
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/wikiwand.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/wikiwand.user.js
// @noframes
// ==/UserScript==

(function() {
    var domains = location.host.split("."); // en.wikipedia.org
    if(domains[0] === "www") domains.shift(); // remove www. in URL
	if(domains[domains.length - 3] == "m") domains.splice(domains.length - 3, 1); // remove m. in URL

    var lang = domains.length <= 2 ? navigator.language.split("-")[0] : domains[0];

    var base = "https://www.wikiwand.com/" + lang + "/";
    var article = location.pathname.substring(1); // remove first slash
	if(article.substring(0, 5) == "wiki/") article = article.substring(5);

	var params = new URLSearchParams(location.search);
	var oldformat = params.get("oldformat") == "true";
	params.delete("oldformat");
    var url = base + article + location.hash + (params.toString() ? "?" + params.toString() : "");

	if(oldformat) {
		window.addEventListener("DOMContentLoaded", function() {
			var el = document.createElement("a");
			el.className = "wikiwand-link";
			el.href = url;
			el.textContent = lang == "fr" ? "(voir sur Wikiwand)" : "(see on Wikiwand)";
			document.querySelector("h1").appendChild(el);

			var el2 = document.createElement("style");
			el2.textContent = ".wikiwand-link {font-size:85%; margin-left:0.3em} @media print {.wikiwand-link {display:none}}";
			document.head.appendChild(el2);
		});
		return;
	}

    location.href = url;
})();
