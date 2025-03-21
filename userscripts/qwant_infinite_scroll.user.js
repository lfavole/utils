// ==UserScript==
// @name         Qwant infinite scroll
// @version      2024-02-27
// @description  Automatically click on the next page button on Qwant.
// @author       Laurent FAVOLE
// @match        https://www.qwant.com/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=qwant.com
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/qwant_infinite_scroll.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/qwant_infinite_scroll.user.js
// @grant        none
// ==/UserScript==

(function() {
    function check_for_next_page_buttons() {
        var buttons = document.querySelectorAll('button[data-testid="buttonShowMore"]');
        if(buttons.length) {
            for(var i = 0, l = buttons.length; i < l; i++) {
                observer.observe(buttons[i]);
            }
        }
    }

    var observer = new IntersectionObserver(obs => {
        for(var i = 0, l = obs.length; i < l; i++) {
            if(obs[i].isIntersecting) {
                obs[i].target.click();
            }
        }
        check_for_next_page_buttons();
    }, {threshold: 0.5});
    setInterval(check_for_next_page_buttons, 500);

    var count = 5;
    var intv = setInterval(function() {
        if(count <= 0) {
            clearInterval(intv);
            return;
        }
        var error_link = document.querySelector(".PagerError a");
        if(error_link) {
            error_link.click();
            count = 0;
            return;
        }
        var buttons = document.querySelectorAll('button[data-testid="buttonShowMore"]');
        if(!buttons.length) return;
        for(var button of buttons) {
            button.click();
        }
        count -= 1;
    }, 3000);
})();
