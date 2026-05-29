// ----- Configuration ------------------------------------------------------
// LANG controls which alphabet is displayed (and which family of audio
// folders is offered in the picker). Each language has one alphabet config
// in ALPHABETS, and one or more "sound/<LANG>-<source>/" folders, listed in
// SOURCES below. A real settings UI will replace LANG later — the in-app
// "Switch audio" chip already swaps the source at runtime.
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
// of "sound/<LANG>-<id>/"; `label` is what the on-screen chip shows. Add a
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

var STORAGE_KEY = "abc-app:source:" + LANG;
// --------------------------------------------------------------------------

$(function () {
    var alpha = ALPHABETS[LANG];
    if (!alpha) { throw new Error("Unknown LANG: " + LANG); }

    var sources = SOURCES[LANG] || [];
    if (!sources.length) { throw new Error("No SOURCES for LANG: " + LANG); }

    // Recall the last source the user picked (default = first in SOURCES).
    var savedId;
    try { savedId = localStorage.getItem(STORAGE_KEY); } catch (_) { savedId = null; }
    var currentIdx = Math.max(0, sources.findIndex(function (s) { return s.id === savedId; }));
    if (currentIdx === -1) currentIdx = 0;

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
    // One Audio per letter for the *currently active* source. Rebuilt when
    // the user taps Switch audio.
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
        try { localStorage.setItem(STORAGE_KEY, src.id); } catch (_) { /* private mode */ }
    }
    loadSounds();

    function playLetter(letter) {
        var audio = sounds[letter];
        if (!audio) return;
        audio.currentTime = 0;
        var p = audio.play();
        if (p && typeof p.catch === "function") {
            p.catch(function () { /* autoplay blocked — ignore */ });
        }
    }

    function flash($key) {
        $key.addClass("pressed");
        setTimeout(function () { $key.removeClass("pressed"); }, 180);
    }

    // ---- Switch-audio chip (current label + cycle button) -----------------
    var $chip = $('<div id="source-chip"></div>')
        .append('<span class="source-name"></span>')
        .append('<button type="button" class="source-switch">Switch audio</button>')
        .appendTo("body");

    function renderChip() {
        $chip.find(".source-name").text(sources[currentIdx].label);
    }
    renderChip();

    $chip.on("pointerdown", ".source-switch", function (e) {
        // Stop the tap from propagating to the keyboard underneath.
        e.preventDefault();
        e.stopPropagation();
        currentIdx = (currentIdx + 1) % sources.length;
        loadSounds();
        renderChip();
    });

    // ---- Input -----------------------------------------------------------
    // Pointer events: single handler covers mouse, touch, pen.
    $kb.on("pointerdown", ".key", function (e) {
        e.preventDefault();
        var letter = $(this).data("letter");
        playLetter(letter);
        flash($(this));
    });

    // Physical keyboard: any letter that exists in this alphabet.
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
