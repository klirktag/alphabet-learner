// ----- Configuration ------------------------------------------------------
// LANG controls which alphabet is displayed (and which family of audio
// folders is offered in the Settings popup). Each language has one alphabet
// config in ALPHABETS and one or more "sound/<LANG>-<source>/" folders
// listed in SOURCES. A real language picker will replace this constant later
// — the in-app Settings popup already swaps audio sources at runtime.
var LANG = "sv";

var ALPHABETS = {
    en: {
        letters: "abcdefghijklmnopqrstuvwxyz",
        rows: [6, 7, 7, 6],
        slugs: {}
    },
    sv: {
        letters: "abcdefghijklmnopqrstuvwxyzåäö",
        rows: [7, 8, 7, 7],
        slugs: { "å": "aa", "ä": "ae", "ö": "oe" }
    }
};

// Audio source folders for each language. Each entry's `id` is the suffix
// of "sound/<LANG>-<id>/"; `label` is what the Settings popup shows. Add a
// new recording set by dropping a folder in sound/ and appending a line here.
var SOURCES = {
    sv: [
        { id: "piper-nst",  label: "Piper nst" },
        { id: "piper-alma", label: "Piper alma" },
        { id: "piper-lisa", label: "Piper lisa" },
        { id: "espeak",     label: "espeak" },
        { id: "recorded",   label: "Inspelat" }
    ],
    en: [
        { id: "espeak",     label: "espeak" }
    ]
};

// Per-letter word associations for the "Visa ord" feature. Each letter maps
// to an *array* of words; on tap one is picked at random. Each entry's
// `folder` is a sound/<LANG>-<source>/words/<folder>/ slug; `label` is the
// proper Swedish spelling shown on screen.
//
// To add a word: drop folders with audio.webm + image.svg under every
// source's words/ subdir (tools/generate_words.py automates this), then
// append a line to the right letter's array.
var WORDS = {
    sv: {
        "a": [{folder:"apa", label:"Apa"}, {folder:"ananas", label:"Ananas"}, {folder:"anka", label:"Anka"}, {folder:"apelsin", label:"Apelsin"}],
        "b": [{folder:"bok", label:"Bok"}, {folder:"banan", label:"Banan"}, {folder:"bil", label:"Bil"}, {folder:"boll", label:"Boll"}, {folder:"blomma", label:"Blomma"}, {folder:"bjoern", label:"Björn"}, {folder:"baat", label:"Båt"}, {folder:"buss", label:"Buss"}],
        "c": [{folder:"cykel", label:"Cykel"}, {folder:"citron", label:"Citron"}],
        "d": [{folder:"docka", label:"Docka"}, {folder:"dator", label:"Dator"}, {folder:"drake", label:"Drake"}],
        "e": [{folder:"eld", label:"Eld"}, {folder:"elefant", label:"Elefant"}, {folder:"ek", label:"Ek"}],
        "f": [{folder:"faagel", label:"Fågel"}, {folder:"fisk", label:"Fisk"}, {folder:"flicka", label:"Flicka"}, {folder:"flygplan", label:"Flygplan"}, {folder:"fjaeril", label:"Fjäril"}],
        "g": [{folder:"gris", label:"Gris"}, {folder:"glass", label:"Glass"}, {folder:"giraff", label:"Giraff"}, {folder:"gitarr", label:"Gitarr"}],
        "h": [{folder:"hus", label:"Hus"}, {folder:"hund", label:"Hund"}, {folder:"hand", label:"Hand"}, {folder:"haest", label:"Häst"}, {folder:"hatt", label:"Hatt"}],
        "i": [{folder:"is", label:"Is"}, {folder:"igelkott", label:"Igelkott"}],
        "j": [{folder:"jul", label:"Jul"}, {folder:"juice", label:"Juice"}, {folder:"jordgubbe", label:"Jordgubbe"}],
        "k": [{folder:"katt", label:"Katt"}, {folder:"kaka", label:"Kaka"}, {folder:"ko", label:"Ko"}, {folder:"kanin", label:"Kanin"}, {folder:"klocka", label:"Klocka"}, {folder:"krokodil", label:"Krokodil"}],
        "l": [{folder:"lampa", label:"Lampa"}, {folder:"lejon", label:"Lejon"}, {folder:"loek", label:"Lök"}],
        "m": [{folder:"mamma", label:"Mamma"}, {folder:"maane", label:"Måne"}, {folder:"mus", label:"Mus"}, {folder:"melon", label:"Melon"}, {folder:"morot", label:"Morot"}],
        "n": [{folder:"napp", label:"Napp"}, {folder:"nyckel", label:"Nyckel"}, {folder:"naesa", label:"Näsa"}],
        "o": [{folder:"orm", label:"Orm"}, {folder:"ost", label:"Ost"}, {folder:"oxe", label:"Oxe"}],
        "p": [{folder:"pappa", label:"Pappa"}, {folder:"paeron", label:"Päron"}, {folder:"pingvin", label:"Pingvin"}, {folder:"peng", label:"Peng"}, {folder:"pizza", label:"Pizza"}, {folder:"panda", label:"Panda"}],
        "r": [{folder:"ros", label:"Ros"}, {folder:"regn", label:"Regn"}, {folder:"ring", label:"Ring"}, {folder:"raev", label:"Räv"}],
        "s": [{folder:"sol", label:"Sol"}, {folder:"sten", label:"Sten"}, {folder:"saeng", label:"Säng"}, {folder:"sko", label:"Sko"}, {folder:"snoe", label:"Snö"}, {folder:"slott", label:"Slott"}],
        "t": [{folder:"tand", label:"Tand"}, {folder:"taag", label:"Tåg"}, {folder:"tiger", label:"Tiger"}, {folder:"tomte", label:"Tomte"}, {folder:"telefon", label:"Telefon"}, {folder:"traktor", label:"Traktor"}],
        "u": [{folder:"uggla", label:"Uggla"}, {folder:"undulat", label:"Undulat"}],
        "v": [{folder:"vatten", label:"Vatten"}, {folder:"varg", label:"Varg"}, {folder:"vante", label:"Vante"}, {folder:"valp", label:"Valp"}, {folder:"vindruva", label:"Vindruva"}],
        "x": [{folder:"xylofon", label:"Xylofon"}],
        "y": [{folder:"yxa", label:"Yxa"}, {folder:"yoghurt", label:"Yoghurt"}],
        "z": [{folder:"zebra", label:"Zebra"}],
        "å": [{folder:"aasna", label:"Åsna"}, {folder:"aar", label:"År"}],
        "ä": [{folder:"aegg", label:"Ägg"}, {folder:"aepple", label:"Äpple"}, {folder:"aelg", label:"Älg"}],
        "ö": [{folder:"oega", label:"Öga"}, {folder:"oern", label:"Örn"}, {folder:"oeken", label:"Öken"}]
    },
    en: {}
};

var STORAGE_KEY_SOURCE = "abc-app:source:" + LANG;
var STORAGE_KEY_WORDS  = "abc-app:show-words:" + LANG;
var WORD_DISPLAY_MS    = 3500;  // auto-dismiss after this many ms
// --------------------------------------------------------------------------

$(function () {
    var alpha = ALPHABETS[LANG];
    if (!alpha) { throw new Error("Unknown LANG: " + LANG); }

    var sources = SOURCES[LANG] || [];
    if (!sources.length) { throw new Error("No SOURCES for LANG: " + LANG); }

    var words = WORDS[LANG] || {};

    // Recall the last source the user picked (default = first in SOURCES).
    var savedSrc;
    try { savedSrc = localStorage.getItem(STORAGE_KEY_SOURCE); } catch (_) { savedSrc = null; }
    var currentIdx = sources.findIndex(function (s) { return s.id === savedSrc; });
    if (currentIdx === -1) currentIdx = 0;

    // Visa ord toggle: defaults ON if no saved preference.
    var showWordsEnabled = (function () {
        try {
            var v = localStorage.getItem(STORAGE_KEY_WORDS);
            return v === null ? true : v === "true";
        } catch (_) { return true; }
    })();

    // ---- Keyboard ---------------------------------------------------------
    var $kb = $("#keyboard").empty();
    var idx = 0;
    alpha.rows.forEach(function (rowLen) {
        var $row = $('<div class="row"></div>');
        for (var j = 0; j < rowLen; j++, idx++) {
            var letter = alpha.letters[idx];
            $('<button class="key" type="button"></button>')
                .attr("data-letter", letter)
                .text(letter.toUpperCase())
                .appendTo($row);
        }
        $row.appendTo($kb);
    });

    // ---- Audio source management ------------------------------------------
    var sounds = {};

    function loadSounds() {
        var src = sources[currentIdx];
        var base = "sound/" + LANG + "-" + src.id + "/";
        sounds = {};
        $kb.find(".key").each(function () {
            var letter = $(this).data("letter");
            var slug = alpha.slugs[letter] || letter;
            var audio = new Audio(base + slug + ".webm");
            audio.preload = "auto";
            sounds[letter] = audio;
        });
        try { localStorage.setItem(STORAGE_KEY_SOURCE, src.id); } catch (_) { /* private */ }
    }
    loadSounds();

    function flash($key) {
        $key.addClass("pressed");
        setTimeout(function () { $key.removeClass("pressed"); }, 180);
    }

    // ---- Word display -----------------------------------------------------
    // When a word is configured for the tapped letter and "Visa ord" is on,
    // we show a translucent overlay with the word's image + label and play
    // the word's audio (instead of the bare letter sound). The overlay's
    // backdrop is pointer-events:none so the keys underneath remain tappable
    // — pressing a new letter swaps the displayed word immediately.
    var $wordDisplay = $(
        '<div id="word-display" hidden>' +
            '<div class="word-card">' +
                '<img class="word-image" alt="">' +
                '<div class="word-label"></div>' +
            '</div>' +
        '</div>'
    ).appendTo("body");
    var $wordImage = $wordDisplay.find(".word-image");
    var $wordLabel = $wordDisplay.find(".word-label");
    var $wordCard  = $wordDisplay.find(".word-card");

    var wordAudio = null;
    var wordTimer = null;
    var letterAudioOnEnded = null;  // tracked so we can cancel chained play

    function hideWord() {
        $wordDisplay.prop("hidden", true);
        if (wordAudio) { try { wordAudio.pause(); } catch (_) {} wordAudio = null; }
        if (wordTimer) { clearTimeout(wordTimer); wordTimer = null; }
    }

    function pickWord(letter) {
        var list = words[letter];
        if (!list || !list.length) return null;
        return list[Math.floor(Math.random() * list.length)];
    }

    function showWord(letter) {
        var word = pickWord(letter);
        if (!word) return false;
        var src = sources[currentIdx].id;
        var base = "sound/" + LANG + "-" + src + "/words/" + word.folder + "/";

        $wordImage.attr("src", base + (word.image || "image.svg"));
        $wordLabel.text(word.label || word.folder);
        $wordDisplay.prop("hidden", false);

        if (wordAudio) { try { wordAudio.pause(); } catch (_) {} }
        wordAudio = new Audio(base + "audio.webm");
        var p = wordAudio.play();
        if (p && typeof p.catch === "function") {
            p.catch(function () { /* autoplay blocked — ignore */ });
        }

        if (wordTimer) clearTimeout(wordTimer);
        wordTimer = setTimeout(hideWord, WORD_DISPLAY_MS);
        return true;
    }

    // Tapping the image (or label) inside the card dismisses early.
    $wordCard.on("pointerdown", function (e) {
        e.preventDefault();
        e.stopPropagation();
        hideWord();
    });

    // playLetter sequences the letter sound, then (if Visa ord is on and a
    // word exists for this letter) a randomly picked word sound + image. The
    // word is scheduled via the letter audio's `ended` handler so the two
    // never overlap; rapid taps cancel any pending word from a previous tap.
    function playLetter(letter) {
        // Cancel anything still queued from a previous tap.
        if (letterAudioOnEnded && letterAudioOnEnded.audio) {
            letterAudioOnEnded.audio.removeEventListener("ended", letterAudioOnEnded.handler);
        }
        letterAudioOnEnded = null;
        if (wordAudio) { try { wordAudio.pause(); } catch (_) {} wordAudio = null; }

        var letterAudio = sounds[letter];
        if (!letterAudio) return;
        letterAudio.currentTime = 0;
        var p = letterAudio.play();
        if (p && typeof p.catch === "function") {
            p.catch(function () { /* autoplay blocked — ignore */ });
        }

        if (showWordsEnabled && words[letter] && words[letter].length) {
            var handler = function () {
                letterAudioOnEnded = null;
                showWord(letter);
            };
            letterAudio.addEventListener("ended", handler, { once: true });
            letterAudioOnEnded = { audio: letterAudio, handler: handler };
        }
    }

    // ---- Settings popup ---------------------------------------------------
    var $cog = $('<button id="settings-cog" type="button" aria-label="Settings">⚙</button>')
        .appendTo("body");

    var $overlay = $(
        '<div id="settings-overlay" hidden>' +
            '<div class="settings-card" role="dialog" aria-label="Settings">' +
                '<button type="button" class="settings-close" aria-label="Close">×</button>' +
                '<h2 class="settings-title">Settings</h2>' +
                '<section class="settings-row">' +
                    '<div class="settings-row-label">Audio</div>' +
                    '<div class="settings-row-control">' +
                        '<span class="source-name"></span>' +
                        '<button type="button" class="source-switch">Switch audio</button>' +
                    '</div>' +
                '</section>' +
                '<section class="settings-row">' +
                    '<div class="settings-row-label">Visa ord</div>' +
                    '<div class="settings-row-control">' +
                        '<button type="button" class="words-toggle" role="switch">' +
                            '<span class="words-toggle-thumb"></span>' +
                        '</button>' +
                    '</div>' +
                '</section>' +
            '</div>' +
        '</div>'
    ).appendTo("body");

    function renderSourceName() {
        $overlay.find(".source-name").text(sources[currentIdx].label);
    }
    function renderWordsToggle() {
        $overlay.find(".words-toggle")
            .toggleClass("on", showWordsEnabled)
            .attr("aria-checked", showWordsEnabled ? "true" : "false");
    }
    renderSourceName();
    renderWordsToggle();

    function openSettings()  { $overlay.prop("hidden", false); }
    function closeSettings() { $overlay.prop("hidden", true); }

    $cog.on("pointerdown", function (e) {
        e.preventDefault();
        e.stopPropagation();
        openSettings();
    });

    $overlay.on("pointerdown", ".settings-close", function (e) {
        e.preventDefault();
        e.stopPropagation();
        closeSettings();
    });

    // Backdrop tap closes (but not card-interior tap).
    $overlay.on("pointerdown", function (e) {
        if (e.target === this) {
            e.preventDefault();
            closeSettings();
        }
    });

    $overlay.on("pointerdown", ".source-switch", function (e) {
        e.preventDefault();
        e.stopPropagation();
        currentIdx = (currentIdx + 1) % sources.length;
        loadSounds();
        renderSourceName();
    });

    $overlay.on("pointerdown", ".words-toggle", function (e) {
        e.preventDefault();
        e.stopPropagation();
        showWordsEnabled = !showWordsEnabled;
        try { localStorage.setItem(STORAGE_KEY_WORDS, String(showWordsEnabled)); } catch (_) {}
        renderWordsToggle();
        if (!showWordsEnabled) hideWord();
    });

    // Escape key closes the popup (handy for desktop).
    $(document).on("keydown", function (e) {
        if (e.key === "Escape") {
            if (!$overlay.prop("hidden")) closeSettings();
            else hideWord();
        }
    });

    // ---- Input -----------------------------------------------------------
    $kb.on("pointerdown", ".key", function (e) {
        e.preventDefault();
        var letter = $(this).data("letter");
        playLetter(letter);
        flash($(this));
    });

    $(document).on("keydown", function (e) {
        if (e.repeat) return;
        var key = (e.key || "").toLowerCase();
        if (key.length !== 1) return;
        var $btn = $kb.find('.key[data-letter="' + key + '"]');
        if (!$btn.length) return;
        playLetter(key);
        flash($btn);
    });
});
