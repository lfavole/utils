// ==UserScript==
// @name         Link checker for student websites
// @version      1.0
// @description  Checks which student websites are active (or not).
// @author       Laurent FAVOLE
// @match        https://*/mod/page/view.php?id=*
// @match        http://*.onlinehome.fr/*
// @downloadURL  https://github.com/lfavole/utils/raw/main/userscripts/student_website_checker.user.js
// @updateURL    https://github.com/lfavole/utils/raw/main/userscripts/student_website_checker.user.js
// @grant        none
// @run-at       document-end
// ==/UserScript==


(() => {
    "use strict";

    // Utility functions

    let formatNumber = n => new Intl.NumberFormat(navigator.language, {maximumSignificantDigits: 3}).format(n);

    let create = (tag, text, link = "") => {
        let startElement = document.createElement(tag.split(".")[0]);
        let element = startElement;
        if (link) {
            let linkElement = document.createElement("a");
            linkElement.href = link;
            element.appendChild(linkElement);
            element = linkElement;
        }
        element.className = (tag.match(/\.(\w+)/g) || []).map(x => x.substring(1)).join(" ");
        element.textContent = text;
        return startElement;
    };

    // Source: https://stackoverflow.com/a/37511463
    let removeAccents = text => text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    let compare = (a, b) => removeAccents(a) == removeAccents(b);

    let formatSize = size => {
        if (isNaN(+size))
            return "";
        let prefixes = ["", "k", "M", "G"];
        while (size >= 1024) {
            size /= 1024;
            prefixes.shift();
        }
        return formatNumber(size) + " " + prefixes[0] + "o";
    };

    // Source: https://stackoverflow.com/a/11550799
    let getWordsNumber = text => text.replace(/<[^>]*>/g, " ").replace(/[-'’]/, "").trim().split(/[^a-z\u00E0-\u00FC]+/gi).length;

    // Part 1: Create the table and display the data
    if (location.pathname.includes("/mod/page/view.php")) {
        if (!document.querySelector("h1")?.textContent.includes("Liste de vos mini-sites"))
            return;

        // columns of the table
        const METADATA = {
            ok:            {name: "❓",     fullName: "Le site fonctionne-t-il ?",                           type: "boolean", fancy: true},
            prenom:        {name: "Prénom", link: true},
            nom:           {name: "Nom",    link: true},
            date:          {name: "Date",   fullName: "Date de première publication du site",                type: "date"},
            htmlFiles:     {name: "FH",     fullName: "Nombre de fichiers HTML",                             type: "number",  crit: x => x == 3},
            htmlComments:  {name: "CH",     fullName: "Nombre de commentaires dans les fichiers HTML",       type: "number",  crit: x => x < 10 ? 0 : x < 50 ? 1 : 0.5},
            cssFiles:      {name: "FC",     fullName: "Nombre de fichiers CSS",                              type: "number",  crit: x => x == 1},
            cssComments:   {name: "CC",     fullName: "Nombre de commentaires dans les fichiers CSS",        type: "number",  crit: x => x < 20 ? 0 : x < 100 ? 1 : 0.5},
            jsFiles:       {name: "FJ",     fullName: "Nombre de fichiers JavaScript",                       type: "number",  crit: x => x == 0},
            jsComments:    {name: "CJ",     fullName: "Nombre de commentaires dans les fichiers JavaScript", type: "number",  crit: (x, d) => d.jsFiles == 0 ? 1 : x < 5 ? 0 : x < 25 ? 1 : 0.5},
            files:         {name: "F",      fullName: "Nombre total de fichiers",                            type: "number",  crit: x => x < 10 ? 1 : x < 20 ? 0.5 : 0},
            fonts:         {name: "Fts",    fullName: "Nombre de polices",                                   type: "number",  crit: x => x == 0 ? 0 : x == 2 || x == 3 ? 1 : 0.5},
            customFonts:   {name: "CF",     fullName: "Nombre de polices personnalisées",                    type: "number"},
            googleFonts:   {name: "GF",     fullName: "Le site utilise-t-il Google Fonts ?",                 type: "boolean"},
            size:          {name: "Taille", fullName: "Taille totale du site",                               type: "size",    crit: x => x < 500 * 1024 ? 0.5 : x < 10 * 1024 ** 2 ? 1 : 0},
            bigFiles:      {name: "Gros",   fullName: "Y a-t-il des gros fichiers (de plus de 1 Mo) ?",      type: "boolean", crit: x => !x},
            firstPerson:   {name: "PP",     fullName: "Le site est-il rédigé à la première personne ?",      type: "boolean", crit: x => x},
            youtubeVideos: {name: "YT",     fullName: "Nombre de vidéos YouTube",                            type: "number",  crit: x => x == 0 ? 0 : x == 1 ? 1 : 0.5},
            externalLinks: {name: "LE",     fullName: "Nombre de liens externes",                            type: "number",  crit: x => x < 5 ? 0 : x < 10 ? 1 : 0.5},
            invalidLinks:  {name: "LI",     fullName: "Nombre de liens incorrects",                          type: "number",  crit: x => x == 0},
            words:         {name: "W",      fullName: "Nombre de mots",                                      type: "number",  crit: x => x < 600 ? 0 : x < 900 ? 0.5 : x < 1500 ? 1 : 0},
            wordsPerPage:  {name: "W/P",    fullName: "Nombre moyen de mots par page",                       type: "number",  crit: x => x < 200 ? 0 : x < 300 ? 0.5 : x < 500 ? 1 : 0},
            namePresent:   {name: "N",      fullName: "Y a-t-il le nom de l'étudiant·e sur son site ?",      type: "boolean", crit: x => x},
        };

        // pop-up that will fetch the data for us
        let w = null;
        // interval to send the links to the pop-up or respawn it
        let intv = null;
        // table rows
        let rows = {};
        // websites data
        let data = {};

        let main = document.querySelector('[role="main"]');
        let links = [...main.querySelectorAll("a")];
        let summary = document.createElement("p");
        summary.textContent = "Chargement...";
        main.querySelector("h3").after(summary);

        let yourName = document.querySelector(".logininfo a")?.textContent || "";

        // create the table
        let table = document.createElement("table");

        // update a specific table row
        let updateRow = href => {
            // find the row to update
            let row = rows[href];
            // highlight the row if it's your website
            row.className = compare(yourName, data[href].prenom + " " + data[href].nom) ? "you" : "";

            let n = 0;
            for (let [key, item] of Object.entries(METADATA)) {
                n++;
                // find the cell and the element (cell or link)
                let cell = row.querySelector("td:nth-child(" + n + ")");
                let element = cell;
                if (item.link) {
                    element = element.querySelector("a");
                    if (!element) {
                        element = document.createElement("a")
                        cell.appendChild(element);
                        element.href = href;
                        element.target = "_blank";
                    }
                }
                // clean up the cell
                cell.className = "";
                cell.title = "";
                element.textContent = "";
                // keep a reference to the value for comparisons or to get the criterion result
                let value = data[href][key];
                // stop early if the value hasn't been filled yet
                if (value == null) {
                    continue;
                }
                let displayValue = value;
                if (item.type == "boolean") {
                    cell.dataset.sort = value == null ? -1 : +value;
                    displayValue = value == null ? "" : (item.fancy ? (value ? "✅" : "❌") : (value ? "Oui" : "Non"));
                }
                // apply specific formats and sorting keys if relevant
                if (item.type == "date") {
                    value = new Date(value);
                    cell.dataset.sort = +value;
                    displayValue = +value ? value.toLocaleDateString() : "";
                    element.title = value.toLocaleString();
                }
                if (item.type == "number") {
                    cell.dataset.sort = value;
                    displayValue = formatNumber(value);
                }
                if (item.type == "size") {
                    cell.dataset.sort = +value;
                    displayValue = formatSize(value);
                }
                // apply a class according to the criterion
                if (item.crit)
                    cell.className = {0: "bad", 0.5: "medium", 1: "good"}[+item.crit(value, data[href])];
                element.textContent = displayValue;
            }
        }

        // create the header
        let thead = document.createElement("thead");
        table.appendChild(thead);
        let row = create("tr");

        for (let item of Object.values(METADATA)) {
            let th = create("th", item.name);
            // add the tooltips
            if (item.fullName)
                th.title = item.fullName;
            // set the sort method for numeric data
            if (item.type == "date" || item.type == "number" || item.type == "size")
                th.dataset.sortMethod = "number";
            row.appendChild(th);
        }
        thead.appendChild(row);

        // create the body
        let tbody = document.createElement("tbody");
        table.appendChild(tbody);

        for (let link of links) {
            // create a row for each website
            let row = create("tr");
            for (let _ of Object.values(METADATA))
                row.appendChild(create("td"));
            tbody.appendChild(row);
            rows[link.href] = row;

            // fill in the first and last name
            let [_, prenom, nom] = link.textContent.match(/^Site d['e]\s*(.*?)\s+(.*)$/) || ["", link.textContent, ""];
            data[link.href] = {
                ...Object.fromEntries(Object.keys(METADATA).map(x => [x, null])),
                prenom,
                nom,
            };
            // update the row to reflect that
            updateRow(link.href);

            // remove the link and its container (the list item
            // or the individual list it is in)
            let toRemove = link;
            while (toRemove == link || toRemove.parentElement.childElementCount == 1)
                toRemove = toRemove.parentElement;
            toRemove.remove();
        }

        // add the table
        summary.after(table);

        let customStyle = document.createElement("style");
        customStyle.textContent = `
        /* Remove the inner scrollbars to be able to see the sticky header */
        div:has(> h3) {overflow: unset !important;}
        table {
            width: 100%;
            border-collapse: collapse;
        }
        thead {
            position: sticky;
            top: 61px;  /* Moodle navbar height */
            background: #fff;
        }
        /* For some reason, borders aren't displayed in sticky mode, so we have to replicate it using a background */
        th {
            background: black;
            background-image: linear-gradient(white, white);
            background-repeat: no-repeat;
            background-position: 1px 1px;
            background-size: calc(100% - 2px) calc(100% - 2px);
        }
        /* Add some borders and padding */
        th, td {
            border: 1px solid black;
            padding: 0.25em 0.35em;
            text-align: center;
        }
        tr:nth-child(2n) {background: #ddd;}
        tr.you {background: #ff8;}
        th:first-child, td:first-child {
            padding: 0.25em;
        }
        /* Reduce the width of the first name and last name, so that everything fits in */
        th:nth-child(2), td:nth-child(2) {max-width: 70px;  text-align: left}
        th:nth-child(3), td:nth-child(3) {max-width: 100px; text-align: left}
        td:nth-child(2), td:nth-child(3) {
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }
        td.bad {background: #ea9999;}
        td.medium {background: #f6b26b;}
        td.good {background: #93c47d;}
        `;
        document.head.appendChild(customStyle);

        // load the Tablesort styles and script
        let style = document.createElement("link");
        style.rel = "stylesheet";
        style.href = "https://cdn.jsdelivr.net/npm/tablesort@5/tablesort.css";
        document.head.appendChild(style);

        let script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/tablesort@5";
        script.addEventListener("load", () => {
            // register a number sorter, because sorting numbers as strings doesn't work
            // e.g. "13" > "120" because "3" > "2"
            Tablesort.extend("number", () => false, (a, b) => +b - +a);
            // sort the table
            new Tablesort(table);
        });
        document.head.appendChild(script);

        window.addEventListener("message", async e => {
            // if there was an error in the pop-up, show it
            if (e.data.error) {
                alert(e.data.error);
                return;
            }
            // if we got all the data, stop sending the URLs to the pop-up and close it
            if (e.data.end) {
                clearInterval(intv);
                w?.close();
                return;
            }
            // otherwise, update the data
            // don't handle other messages
            if (!e.data.page) return;
            // don't add the page property, it's not needed
            let href = e.data.page;
            data[href] = {
                ...data[href],
                ...e.data,
            };
            updateRow(href);
            // update the total stats
            let working = Object.values(data).filter(x => x.ok).length;
            let total = Object.values(data).filter(x => x.ok != null).length;
            // don't do a division by zero
            if (total == 0) return;
            summary.textContent = (
                working
                + " site" + (working >= 2 ? "s" : "")
                + " fonctionnel" + (working >= 2 ? "s" : "")
                + " sur " + total
                + " (" + formatNumber(working / total * 100) + " %)"
            );
        });

        window.addEventListener("unload", () => w?.close());

        intv = setInterval(() => {
            if (w && !w.closed) {
                // if the window is open, send the links to it
                // w.postMessage(links.map(link => link.href), "*");
                w.postMessage(Object.entries(data).map(([link, obj]) => ({...obj, link})), "*");
            } else {
                // choose a random website to open
                let url = new URL(links[Math.floor(Math.random() * links.length)].href);
                // add a special URL parameter, so that the script doesn't run for normal visits
                url.search += (url.search.includes("?") ? "&" : "?") + "test=1";
                // open it in a small pop-up
                w = window.open(url, "_blank", "popup=1,location=no,toolbar=no,menubar=no,width=100,height=100");
            }
        }, 500);
    }

    // Part 2: Gather the data from an insecure origin
    // Iframes don't work because of mixed content, so opening a pop-up is the only way
    if (location.host.includes("onlinehome.fr")) {
        // don't run the script for legitimate website visits
        if (new URLSearchParams(location.search).get("test") != "1")
            return;

        let started = false;
        window.addEventListener("message", async e => {
            // only run once
            if (started) return;
            started = true;

            // remove anchors and add /index.html to all links in order to avoid duplicates
            let fixLink = (link, origin) => {
                // flag invalid links
                try {
                    new URL(link, origin);
                } catch(e) {
                    return "invalid";
                }
                return (new URL(link, origin) + "").replace(/#.*$/, "").replace(/\/(?:index\.html)?$/, "/index.html")
            };

            // get the results for all the pages, don't stop at the first error
            await Promise.allSettled(e.data.map(async origObject => {
                let origStartPage = origObject.link;
                // We need to keep origStartPage as it's the key
                // to add the data back into the table

                // first page to be fetched, to check if we are on the same domain
                let startPage = fixLink(origStartPage.replace(/(?<!\/)$/, "/"));
                // metadata about files
                let files = {};
                // files to fetch
                let pendingFiles = [startPage];
                // current file
                let file = null;
                // unique used Google fonts
                let usedGoogleFonts = new Set();
                // unique external links
                let externalLinks = new Set();
                // total words in the navigation bar and in the footer
                let totalNavWords = 0;
                let totalFooterWords = 0;
                while (file = pendingFiles.shift()) {
                    // don't continue if we already have the information
                    if (files[file])
                        continue;
                    // create the variable here, and not in the try block,
                    // to be able to use it afterwards
                    let resp;
                    try {
                        // download the file, fail on network errors or error statuses
                        resp = await fetch(file);
                        if (!resp.ok)
                            throw new Error();
                    } catch(e) {
                        // if it's the first page, send the failure and stop here
                        if (!Object.keys(files).length) {
                            opener.postMessage({page: origStartPage, ok: false}, "*");
                            return;
                        }
                        // save that it's an invalid link and continue to the next link
                        files[file] = {invalidLinks: 1};
                        continue;
                    }
                    // send the success as early as possible to update the table
                    if (!Object.keys(files).length)
                        opener.postMessage({page: origStartPage, ok: true}, "*");

                    // save information about the file
                    let fileInfo = {};
                    files[file] = fileInfo;

                    let contentType = resp.headers.get("Content-Type") || "";
                    // response text, if it's relevant
                    let text = contentType.includes("text/") ? await resp.text() : "";
                    // used Google fonts
                    usedGoogleFonts = new Set([
                        ...usedGoogleFonts,
                        ...[
                            ...(text.match(/(["'])(https?:\/\/fonts\.google.*?)\1/) || ["", "", ""])[2]
                            .matchAll(/(?:family=|\|)([\w+]+)/g)
                        ].map(x => x[1].replace("+", " ")),
                    ]);

                    fileInfo.date = new Date(resp.headers.get("Last-Modified"));
                    fileInfo.size = text.length || (await resp.blob()).size;
                    // this will be counted in the total at the end
                    fileInfo.files = 1;

                    // all links in the webpage/file
                    let links = [];
                    // YouTube video IDs to deduplicate links (<iframe src="..."> is also counted as a link)
                    let youtubeIds = [];

                    if (contentType.includes("text/html")) {
                        links = [...text.matchAll(/(?:href|src)=(["'])(.*?)\1/g)].map(x => x[2]);
                        fileInfo.htmlFiles = 1;
                        fileInfo.cssFiles = (text.match(/<style/g) || []).length;
                        fileInfo.htmlComments = (text.match(/<!--/g) || []).length;
                        fileInfo.firstPerson = (text.match(/je |j'/g) || []).length >= 5;
                        youtubeIds = [...text.matchAll(/<iframe[^>]+src=(["']).*?youtube.*\/(.+?)\1/gs)].map(x => x[2]);
                        fileInfo.youtubeVideos = youtubeIds.length;

                        let bodyContent = (text.match(/(?:<body[^>]*>|^)(.*?)(?:<\/body>|$)/s) || ["", text])[1];
                        let navContent = "";
                        let footerContent = "";
                        bodyContent = bodyContent.replace(/<nav[^>]*>(.*?)<\/nav>/s, (_, c) => (navContent = c, ""));
                        bodyContent = bodyContent.replace(/<footer[^>]*>(.*?)<\/footer>/s, (_, c) => (footerContent = c, ""));

                        // Source: https://stackoverflow.com/a/6969486
                        fileInfo.namePresent = !!removeAccents(bodyContent).match(new RegExp(removeAccents(origObject.prenom).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));

                        totalNavWords += getWordsNumber(navContent);
                        fileInfo.words = fileInfo.wordsPerPage = getWordsNumber(bodyContent);
                        totalFooterWords += getWordsNumber(footerContent);

                    } else if (contentType.includes("text/css")) {
                        links = [...text.matchAll(/@import\s+url\((["']?)(.*?)\1\)/g)].map(x => x[2]);
                        fileInfo.cssFiles = 1;
                        fileInfo.cssComments = (text.match(/\/\*/g) || []).length;
                        fileInfo.fonts = fileInfo.customFonts = (text.match(/@font-face\s*\{/) || []).length;

                    } else if (contentType.includes("text/javascript")) {
                        links = [...text.matchAll(/import(?:\s.*?from\s+)?\(?(["'])(.*?)\1\)?/g)].map(x => x[2]);
                        fileInfo.jsFiles = 1;
                        fileInfo.jsComments = (text.match(/\/\*|\/\//g) || []).length;

                    } else {
                        fileInfo.bigFiles = fileInfo.size > 1024 ** 2;
                    }

                    // check for incorrectly formed URLs
                    let invalidLinks = 0;
                    links = links.map(x => fixLink(x, file)).filter(x => {
                        if (x == "invalid") {
                            invalidLinks++;
                            return false;
                        }
                        return x;
                    });
                    fileInfo.invalidLinks = invalidLinks;
                    // save the list of files to check next
                    pendingFiles.push(...links.filter(page => new URL(page).host == new URL(startPage).host));
                    // add the external links
                    externalLinks = new Set([...externalLinks, ...links.filter(page => {
                        if ([...youtubeIds, "fonts.google", "pixabay.com", "unsplash.com"].some(x => page.includes(x)))
                            return;
                        return new URL(page).protocol.includes("http") && new URL(page).host != new URL(startPage).host;
                    })]);

                    // check for the oldest file, it's the only way to get an approximation of the website creation date
                    let date = Object.values(files).map(x => x.date).filter(x => x).sort()[0];
                    let ret = {
                        page: origStartPage,
                        ok: true,
                        date: +date,
                        externalLinks: externalLinks.size,
                        // count the Google fonts that are used on all the pages
                        fonts: usedGoogleFonts.size,
                        googleFonts: usedGoogleFonts.size > 0,
                        words: totalNavWords + totalFooterWords,
                        wordsPerPage: totalNavWords + totalFooterWords,
                    };
                    // sum up the number of items for those properties
                    for (let prop of [
                        "htmlComments",
                        "cssComments",
                        "jsComments",
                        "fonts",
                        "customFonts",
                        "size",
                        "htmlFiles",
                        "cssFiles",
                        "jsFiles",
                        "files",
                        "youtubeVideos",
                        "invalidLinks",
                        "words",
                    ]) {
                        ret[prop] = Object.values(files).map(x => x[prop]).reduce((a, b) => (a || 0) + (b || 0), ret[prop] || 0);
                    }
                    // average up the number of items for those properties
                    for (let prop of ["wordsPerPage"]) {
                        let n = 0;
                        let toAdd = Object.values(files).map(x => x[prop]).reduce((a, b) => {
                            if (b == null)
                                return a;
                            n++;
                            return a + b;
                        }, 0);
                        if (n)
                            toAdd /= n;
                        ret[prop] = (ret[prop] || 0) + toAdd;
                    }
                    // check if at least one file fulfills the property for those properties
                    for (let prop of ["bigFiles", "firstPerson", "namePresent"]) {
                        ret[prop] = Object.values(files).some(x => x[prop]);
                    }
                    opener.postMessage(ret, "*");
                }
            }).map(promise => promise.catch(error => opener.postMessage({error}, "*"))));
            // wait 1 second, so that the last messages are received
            await new Promise(resolve => setTimeout(resolve, 1000));
            // ask for the window to be closed
            opener.postMessage({end: true}, "*");
        });

        // close the pop-up if we closed the main window
        // inspired from https://stackoverflow.com/a/55601462
        setInterval(() => {
            if (!window.opener || window.opener?.closed)
                window.close();
        }, 500);
    }
})();
