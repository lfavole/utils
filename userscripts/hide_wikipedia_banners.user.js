// ==UserScript==
// @name         Hide banners on Wikipedia
// @namespace    http://tampermonkey.net/
// @version      2024-03-01
// @description  Automatically click on the close button of the Wikipedia banners.
// @author       Laurent FAVOLE
// @match        https://*.wikimedia.org/*
// @match        https://*.wikipedia.org/*
// @match        https://*.wiktionary.org/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=wikipedia.org
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/hide_wikipedia_banners.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/hide_wikipedia_banners.user.js
// @grant        none
// ==/UserScript==

(function() {
    var intv = setInterval(function() {
        try {
            mw.centralNotice.hideBanner();
            clearInterval(intv);
        } catch(err) {}
    }, 500);
    setTimeout(() => clearInterval(intv));
})();
