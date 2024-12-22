// ==UserScript==
// @name         Kahoot! quizzes administration automation
// @version      2024-02-25
// @description  Automatically log me in with Google on Kahoot!, hides the upgrade pages, sets the search language to French and add the "*" key to add favorite quizzes.
// @author       Laurent FAVOLE
// @match        https://kahoot.com/upgrade/*
// @match        https://create.kahoot.it/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=kahoot.it
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/auto_create_kahoot.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/auto_create_kahoot.user.js
// @grant        none
// ==/UserScript==

(function() {
    if(location.pathname.startsWith("/go/upgrade") || location.pathname.startsWith("/upgrade")) {
        history.back();
        return;
    }
    if(location.pathname.startsWith("/auth/login")) {
        var login_countdown = 3;
        var login_countdown_element = document.createElement("span");
        login_countdown_element.style.display = "inline-block";
        login_countdown_element.style.marginLeft = "0.2em";
        login_countdown_element.style.width = "1.5em";
        login_countdown_element.style.textAlign = "left";

        document.addEventListener("keydown", function(evt) {
            if(evt.key == "Escape" && login_countdown != Infinity) {
                evt.preventDefault();
                clearInterval(login_intv);
                login_countdown = Infinity;
                login_countdown_element.remove();
            }
        }, true);

        var login_intv = setInterval(function() {
            var login_button = document.querySelector('button[data-functional-selector="log-in-google-button"]');
            if(!login_button) return;

            var title = document.querySelector('h1[class^="card__WideCardTitle"]');
            if(!title) return;
            if(!document.body.contains(login_countdown_element)) {
                title.appendChild(login_countdown_element);
            }
            if(login_countdown > 0) {
                login_countdown_element.textContent = "(" + login_countdown + ")";
                login_countdown--;
            } else {
                login_countdown_element.remove();
                login_button.click();
                clearInterval(login_intv);
            }
        }, 1000);
        return;
    }

    var intv = setInterval(function() {
        var banner = document.querySelector('aside[data-functional-selector="top-strip"]');
        if(!banner || !banner.innerText.includes("Offer")) return;

        var close_button = banner.querySelector('button[data-functional-selector="top-strip__close-button__icon-button"]');
        if(!close_button) return;
        close_button.click();
        clearInterval(intv);
    }, 250);

    setTimeout(() => clearInterval(intv), 15000);

    function fixURL() {
        if(!location.pathname.startsWith("/search-results/")) return;
        var new_url = "";
        if(location.pathname == "/search-results/all") new_url = "kahoots";
        var usp = new URLSearchParams(location.search);
        if(!usp.get("language")) usp.set("language", "Français");
        if(!usp.get("inventoryItemId")) usp.set("inventoryItemId", "NONE");

        history.replaceState(null, "", new_url + "?" + usp);
    }
    window.addEventListener("popstate", fixURL);

    var oldURL = location.href;
    setInterval(function() {
        if(location.href != oldURL) {
            oldURL = location.href;
            fixURL();
        }
    }, 500);
    fixURL();

    document.addEventListener("keydown", function(evt) {
        if(evt.key == "*") {
            var star = document.querySelector('button[class*="favorite-star__AddFavButton"], button[class*="favorite-star__RemoveFavButton"]')
            if(!star) {
                alert("No star");
                return;
            }
            star.click();
        }
    }, true);
})();
