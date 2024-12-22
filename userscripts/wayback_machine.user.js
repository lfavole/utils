// ==UserScript==
// @name         Wayback Machine
// @version      2024-04-08
// @description  Like the Wayback Machine extension, but cheaper.
// @author       Laurent FAVOLE
// @match        *://*/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=archive.org
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/wayback_machine.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/wayback_machine.user.js
// @grant        GM_xmlhttpRequest
// @connect      firefox-api.archive.org
// ==/UserScript==

(function() {
    // Use this instead of encodeURIComponent()
    function fixedEncodeURIComponent(str) {
        return encodeURIComponent(str).replace(/[!'()*]/g, c => "%" + c.charCodeAt(0).toString(16))
    }

    // Makes sure response is a valid URL to prevent code injection
    function isValidUrl(url) {
        return typeof url === 'string' && url.match(/https?:\/\//)
    }

    // Checks Wayback Machine API for url snapshot
    function wmAvailabilityCheck(url) {
        console.log("Checking for", url)
        GM_xmlhttpRequest({
            url: "https://firefox-api.archive.org/wayback/available?url=" + fixedEncodeURIComponent(url),
            method: "GET",
            headers: {
                "Accept": "application/json"
            },
            onload: response => {
                let json = JSON.parse(response.responseText)
                console.log("JSON parsed")
                console.log(json)
                if (json && json.archived_snapshots &&
                    json.archived_snapshots.closest &&
                    json.archived_snapshots.closest.available &&
                    json.archived_snapshots.closest.available === true &&
                    json.archived_snapshots.closest.status.indexOf("2") === 0 &&
                    isValidUrl(json.archived_snapshots.closest.url)) {
                    let wayback_url = json.archived_snapshots.closest.url.replace(/^http:/, "https:")
                    let timestamp = json.archived_snapshots.closest.timestamp
                    console.log("wayback_url =", wayback_url)
                    console.log("timestamp =", timestamp)
                    if (wayback_url !== null) {
                        let ret = confirm("View archived version?")
                        if (ret) location.href = wayback_url
                    }
                }
            }
        })
    }

    if (document.title.match(/\b([45]\d\d|not found|server error)\b/i)) {
        wmAvailabilityCheck(location.href)
        return
    }

    fetch(location.href)
        .then((response) => {
        console.log("response.status =", response.status)
        if (response.status >= 400) wmAvailabilityCheck(location.href)
    })
})();
