// ==UserScript==
// @name         Autofocus username/password field
// @version      2024-05-24
// @description  Set the focus on the first username (or password) field automatically on page load.
// @match        *://*/*
// @run-at       document-start
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/autofocus_password.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/autofocus_password.user.js
// @grant        none
// ==/UserScript==

window.addEventListener("DOMContentLoaded", function() {
    var inputs = [].filter.call(document.querySelectorAll("input:is([type=text], [type=username], [type=email], [type=password])"), function(e) {
        return e.style.display != "none";
    }); // all the inputs on the webpage
    if(!inputs) return;

    var pwdinput = document.querySelector("input[type=password]"); // the first password input
    var username_names = ["user", "username", "login", "identifiant", "identifier"]; // words that are contained in a username field name/ID

    for(let input, i = 0, l = inputs.length; i < l; i++) {
        input = inputs[i];
        if(input == pwdinput) {
            // we found the first password input
            if(i == 0) {
                // first password field = no username field before, so we focus the password field
                inputs[i].focus();
                break;
            }
            if(inputs[i - 1].type == "email"
               || username_names.some(name => {
                return (
                    inputs[i - 1].name.match(RegExp("\\b" + name + "\\b"))
                    || inputs[i - 1].id.match(RegExp("\\b" + name + "\\b"))
                );
            })
              ) {
                // there is a username field before the password field, we focus it
                inputs[i - 1].focus();
                break;
            }
        }
    }
});
