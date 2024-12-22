// ==UserScript==
// @name         Automatic Google OAuth login
// @version      2024-03-01
// @description  Click on my email on some Google logins (currently Tampermonkey and Kahoot!).
// @author       Laurent FAVOLE
// @match        https://accounts.google.com/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=google.com
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/auto_google_login.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/auto_google_login.user.js
// @grant        none
// ==/UserScript==

(function() {
    var usp = new URLSearchParams(location.search);
    if(!(usp.get("redirect_uri") || "").match(/^https?:\/\/[^\/]*(tampermonkey.net|create.kahoot.it)\//)) return;

    var countdown_element;
    var countdown = 3;
    setInterval(function() {
        var me = document.querySelector('[data-identifier*="laurent"][data-identifier*="favole"]');
        if(!me) return;

        var header = document.querySelector("h1");
        if(!header) return;
        if(!countdown_element) {
            countdown_element = document.createElement("span");
            countdown_element.style.display = "inline-block";
            countdown_element.style.marginLeft = "0.2em";
            countdown_element.style.display = "inline-block";
            countdown_element.style.width = "1.5em";
            countdown_element.style.textAlign = "left";
            header.appendChild(countdown_element);
        }

        if(countdown > 0) {
            countdown_element.textContent = "(" + countdown + ")";
            countdown--;
        } else {
            header.removeChild(countdown_element);
            me.click();
        }
    }, 1000);
})();
