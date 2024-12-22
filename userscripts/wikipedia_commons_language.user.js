// ==UserScript==
// @name         Change Wikimedia Commons language
// @version      2024-03-01
// @description  Automatically set the Wikimedia Commons language to the current browser language.
// @author       Laurent FAVOLE
// @match        https://commons.wikimedia.org/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=wikimedia.org
// @run-at       document-start
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/wikipedia_commons_language.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/wikipedia_commons_language.user.js
// @grant        none
// ==/UserScript==

(function() {
    var language = navigator.language.split("-")[0];
    if(language == "en") return;

    var usp = new URLSearchParams(location.search);
    if(!usp.has("uselang")) {
        usp.set("uselang", language);
        location.search = usp;
    }
})();
