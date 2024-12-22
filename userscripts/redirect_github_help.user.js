// ==UserScript==
// @name         Automatically redirect GitHub help pages
// @version      2024-02-29
// @description  Automatically redirect to the translated version of GitHub help pages.
// @author       Laurent FAVOLE
// @match        https://docs.github.com/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=docs.github.com
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/redirect_github_help.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/redirect_github_help.user.js
// @grant        none
// ==/UserScript==

(function() {
    var intv = setInterval(function() {
        var link = document.querySelector('div.flash[data-type="TRANSLATION"] a');
        if(link) link.click();
    }, 500);

    setTimeout(function() {
        clearInterval(intv);
    }, 15000);
})();
