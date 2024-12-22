// ==UserScript==
// @name         Link to accepted answer on StackExchange sites
// @version      2024-03-08
// @description  Add a direct link to the accepted answer on StackExchange sites.
// @author       Laurent FAVOLE
// @match        https://*.askubuntu.com/*
// @match        https://*.mathoverflow.com/*
// @match        https://*.serverfault.com/*
// @match        https://*.stackapps.com/*
// @match        https://*.stackexchange.com/*
// @match        https://*.stackoverflow.com/*
// @match        https://*.superuser.com/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=stackoverflow.com
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/stackexchange_link.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/stackexchange_link.user.js
// @grant        none
// ==/UserScript==

(async function() {
    var match = location.pathname.match(/\/questions\/(\d+)/);
    if(!match) return
    var question_id = +match[1];

    var parts = location.host.split(".");
    var site = parts.shift();
    if(site == "www") site = parts.shift();

    var answerCount = document.querySelector(".answers-subheader h2");
    var acceptedAnswer = document.querySelector(".accepted-answer");
    answerCount.appendChild(document.createTextNode(" – "));

    var acceptedAnswerLink = document.createElement("a");

    if(acceptedAnswer) {
        // the accepted answer is displayed = we add a link to it
        acceptedAnswerLink.href = "#" + acceptedAnswer.id.replace("answer-", "");
        acceptedAnswerLink.textContent = "go to the accepted answer";
        answerCount.appendChild(acceptedAnswerLink);
    } else {
        var acceptedAnswerSpan = document.createElement("span");
        answerCount.appendChild(acceptedAnswerSpan);

        // no pagination = we don't need to check for an accepted answer
        if(!document.querySelector(".s-pagination")) {
            acceptedAnswerSpan.textContent = "no accepted answer";
            return;
        }

        acceptedAnswerLink.textContent = "no accepted answer (fetching...)";

        var req = await fetch(`https://api.stackexchange.com/2.3/questions/${question_id}/answers?pagesize=100&site=${site}&filter=!szz.51CUjr4j3D))YMWvsnSf6i_MRCp`);
        var data = await req.json();
        for(var item, i = 0, l = data.items.length; i < l; i++) {
            item = data.items[i];
            if(item.is_accepted) {
                acceptedAnswerLink.href = "/a/" + item.answer_id;
                acceptedAnswerLink.textContent = "go to the accepted answer";
                answerCount.appendChild(acceptedAnswerLink);
                break;
            }
        }
    }
})().catch(console.error);
