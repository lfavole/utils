// ==UserScript==
// @name         Kahoot! quizzes gameplay automation
// @version      2024-02-29
// @description  Automatically skip most of the screens and banners and set max volume on Kahoot! quizzes.
// @author       Laurent FAVOLE
// @match        https://play.kahoot.it/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=kahoot.it
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/auto_play_kahoot.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/auto_play_kahoot.user.js
// @grant        none
// ==/UserScript==

(function() {
    window.addEventListener("DOMContentLoaded", function() {
        var el = document.createElement("style");
        el.textContent = `
.countdown {
    display: inline-block;
    line-height: 1em;
    width: 1.5em;
    text-align: center;
    z-index: 1;
}
.countdown.move {
    color: transparent;
    position: relative;
    overflow: hidden;
}
.countdown.move::before, .countdown.move::after {
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    bottom: 0;
    text-align: center;
    animation: 0.4s ease-in-out;
}
.countdown.move::before {
    content: attr(data-before);
    color: white;
    color: var(--color, white);
    animation-name: before;
    opacity: 0;
}
.countdown.move::after {
    content: attr(data-after);
    color: white;
    color: var(--color, white);
    animation-name: after;
}
@keyframes before {
    0% {
        top: 0;
        opacity: 1;
    }
    100% {
        top: -100%;
        opacity: 0;
    }
}
@keyframes after {
    0% {
        top: 100%;
        opacity: 0;
    }
    100% {
        top: 0;
        opacity: 1;
    }
}

[class^="island-selection__IslandsBlockHeader"] .countdown {
    font-size: 24px;
    font-size: 3vmin;
    font-size: clamp(18px, 3vmin, 36px);
    font-weight: bold;
    margin: -0.5em 0;
}

[class^="start-button__StartButtonWrapper"] .countdown {
    font-size: 2em;
    padding: 0 0.25em;
}

[class^="lobbystyles__StartWrapper"] .countdown {
    font-size: 2.5em;
    padding: 0 0.25em;
    --color: black;
    font-weight: bold;
    background-color: white;
    box-shadow: rgba(0, 0, 0, 0.15) 0px 2px 4px;
    border-radius: 4px;
    font-size: 2rem;
    width: 2ch;
    text-align: center;
    margin: 0 0 8px 8px;
}
[class^="lobbystyles__StartWrapper"] .countdown:not(.move),
[class^="lobbystyles__StartWrapper"] .countdown.move::before,
[class^="lobbystyles__StartWrapper"] .countdown.move::after {
    padding: 0.0625em 0.25em;
}

[class^="top-bar__RightButtons"]:has(.countdown), [class^="content-block__ButtonWrapper"]:has(.countdown) {
    flex-direction: row-reverse;
    align-items: flex-start;
}
[class^="top-bar__RightButtons"]:has(.countdown) > *, [class^="content-block__ButtonWrapper"]:has(.countdown) > * {
    margin: 0 !important;
    margin-left: 1em !important;
}
[data-functional-selector="next-button"] {
    flex: 0 0;
}
[class^="top-bar__RightButtons"] .countdown {
    --color: black;
    font-weight: bold;
    background-color: white;
    box-shadow: rgba(0, 0, 0, 0.15) 0px 2px 4px;
    border-radius: 4px;
    font-size: 2rem;
    width: 2ch;
    text-align: center;
}
[class^="top-bar__RightButtons"] .countdown,
[class^="top-bar__RightButtons"] .countdown.move::before,
[class^="top-bar__RightButtons"] .countdown.move::after {
    padding: 0.25em 0.25em;
}
`;
        document.head.appendChild(el);
    });

    var Countdowns = [
        {
            name: "island",
            timer: () => 3,
            container: () => document.querySelector('[class^="island-selection__IslandsBlockHeader"]'),
            isActive: () => document.querySelector('[class^="island-item__Item"]'),
            handle: () => {
                document.querySelector('[class^="island-item__Item"] button').click();
            },
        },

        {
            name: "gamemode",
            timer: () => 3,
            init: () => {
                tryToClick('[data-functional-selector="winter-mode-card"]');

                tryToClick('[data-functional-selector="claim-island-reward"]');

                // hide the sidebar during the ranking
                tryToClick('[class*="styles__SidebarButton"]', () => {
                    tryToClick('[data-functional-selector="show-podium-button"]');
                });
            },
            container: () => document.querySelector('[class^="start-button__StartButtonWrapper"]'),
            isActive: () => document.querySelector('[class^="start-button__ButtonWrapper"] [data-functional-selector$="-button"]'),
            handle: () => {
                document.querySelector('[class^="start-button__ButtonWrapper"] [data-functional-selector$="-button"]').click();
            },
        },

        {
            name: "players",
            timer: () => 60,
            container: () => document.querySelector('[class^="lobbystyles__StartWrapper"]'),
            isActive: () => +(document.querySelector('[class^="player-counter__PlayerCountText"]') || {}).textContent > 0,
            status: () => +(document.querySelector('[class^="player-counter__PlayerCountText"]') || {}).textContent,
            handle: () => {
                document.querySelector('[class^="enter-button__ButtonContainer"] button').click();
            },
        },

        {
            name: "question",
            timer: () => {
                var title_element = document.querySelector('[class^="question-title__Title"]');
                if(title_element && title_element.textContent == "Tableau des scores") {
                    // leaderboard = 2 seconds countdown
                    return 2;
                } else {
                    return 5;
                }
            },
            container: () => document.querySelector('[class^="top-bar__RightButtons"]'),
            isActive: () => {
                return (
                    document.querySelector('[data-functional-selector="next-button"]')
                    && !document.querySelector('[class*="skip-button__SkipButton"]')
                );
            },
            handle: () => {
                document.querySelector('[data-functional-selector="next-button"]').click();
            },
            next: () => 1,
        },
    ];

    function tryToClick(query, callback) {
        var intv = setInterval(function() {
            // hide the sidebar during the ranking
            var element = document.querySelector(query);
            if(!element) return;
            console.log("Clicking on %s", query);
            element.click();
            clearInterval(intv);
            if(callback) {
                callback();
            }
        }, 500);
    }

    var volume_intv = setInterval(function() {
        if(!document.getElementById("volume-controller-icon")) return;
        console.log("Setting volume");
        // eslint-disable-next-line no-undef
        Howler.volume(1);
        // increase the volume (but this doesn't update the control on the bottom)
        clearInterval(volume_intv);
    }, 500);

    var current_countdown = 0;
    var countdown_element = null;
    var countdown_timer = Countdowns[current_countdown].timer();
    var countdown_status = NaN;

    function changeCountdown() {
        countdown_timer = Countdowns[current_countdown].timer();
        if(Countdowns[current_countdown].init) {
            Countdowns[current_countdown].init();
        }
    }

    var defaultNext = (pos) => pos + 1;

    setInterval(() => {
        if(!Countdowns[current_countdown]) {
            console.log("All countdowns have been used, restarting to 0");
            current_countdown = 0;
            changeCountdown();
        }

        if(countdown_timer == -1) {
            console.log("%s countdown has been stopped", Countdowns[current_countdown].name);
            return;
        }

        if(document.querySelector('div[tabindex="0"] + div div[class^="styles__MenuWrapperAbsolute"]')) {
            console.log("Options are opened, stopping");
            return;
        }

        if(document.querySelector('[role="dialog"]')) {
            console.log("Dialog is opened, stopping");
            return;
        }

        if(!Countdowns[current_countdown].isActive()) {
            var newPos = (Countdowns[current_countdown].next || defaultNext)(current_countdown);
            if(Countdowns[newPos] && Countdowns[newPos].isActive()) {
                current_countdown = newPos;
                changeCountdown();
                console.log("Next countdown (%s) is active, switching to it", Countdowns[current_countdown].name);
            } else {
                console.log("%s countdown is not active", Countdowns[current_countdown].name);
                countdown_timer = Countdowns[current_countdown].timer();
                return;
            }
        }

        if(Countdowns[current_countdown].status) {
            var old_status = countdown_status;
            countdown_status = Countdowns[current_countdown].status();
            console.log("Updated %s countdown status to %s", Countdowns[current_countdown].name, countdown_status);

            if(old_status != countdown_status) {
                console.log("%s countdown status changed from %s to %s, resetting", Countdowns[current_countdown].name, old_status, countdown_status);
                countdown_timer = Countdowns[current_countdown].timer();
            }
        }

        if(countdown_element == null || !document.body.contains(countdown_element)) {
            console.log("Creating %s countdown element", Countdowns[current_countdown].name);
            countdown_element = document.createElement("span");
            countdown_element.className = "countdown";
            Countdowns[current_countdown].container().appendChild(countdown_element);
        }

        if(countdown_timer > 0) {
            console.log("Decreasing %s countdown to %d", Countdowns[current_countdown].name, countdown_timer);
            countdown_element.classList.add("move");
            countdown_element.dataset.before = countdown_element.textContent;
            countdown_element.dataset.after = countdown_timer;
            countdown_element.textContent = countdown_timer;
            setTimeout(() => countdown_element.classList.remove("move"), 400);
            countdown_timer--;
        } else {
            console.log("%s countdown reached its end, running handler", Countdowns[current_countdown].name);
            Countdowns[current_countdown].handle();
        }
    }, 1000);

    document.addEventListener("keydown", function(evt) {
        if(evt.key == "Escape" && countdown_timer != -1) {
            evt.preventDefault();
            console.log("Canceling %s countdown", Countdowns[current_countdown].name);
            countdown_timer = -1;
            countdown_element.remove();
            countdown_element = null;
        }
        if(evt.key == "+") {
            evt.preventDefault();
            if(countdown_timer != -1) {
                console.log("Cancelling %s countdown", Countdowns[current_countdown].name);
                countdown_timer = -1;
            } else {
                console.log("Resuming %s countdown", Countdowns[current_countdown].name);
                countdown_timer = Countdowns[current_countdown].timer();
            }
        }
    }, true);
})();