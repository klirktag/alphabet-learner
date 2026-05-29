// ----- Configuration ------------------------------------------------------
// Change LANG to switch the alphabet + voice. Each language must have a
// matching sound/<LANG>/ folder. (A real settings UI will replace this.)
var LANG = "sv";

// Per-language alphabet, keyboard layout (rows of N keys each, summing to
// alphabet length), and slug map for letters whose filename can't be the
// letter itself. The slug is what looks up sound/<LANG>/<slug>.webm.
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
// --------------------------------------------------------------------------

$(function () {
    var alpha = ALPHABETS[LANG];
    if (!alpha) { throw new Error("Unknown LANG: " + LANG); }

    // Build the keyboard rows from the alphabet + layout config.
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

    // Pre-load one Audio object per letter so playback is instant on tap.
    var sounds = {};
    $kb.find(".key").each(function () {
        var letter = $(this).data("letter");
        var slug = alpha.slugs[letter] || letter;
        var audio = new Audio("sound/" + LANG + "/" + slug + ".webm");
        audio.preload = "auto";
        sounds[letter] = audio;
    });

    function playLetter(letter) {
        var audio = sounds[letter];
        if (!audio) return;
        // Rewind so rapid repeated taps always start from the beginning.
        audio.currentTime = 0;
        var p = audio.play();
        if (p && typeof p.catch === "function") {
            p.catch(function () { /* browser blocked autoplay — ignore */ });
        }
    }

    function flash($key) {
        $key.addClass("pressed");
        setTimeout(function () { $key.removeClass("pressed"); }, 180);
    }

    // Pointer events cover mouse + touch + pen with a single handler.
    $kb.on("pointerdown", ".key", function (e) {
        e.preventDefault();
        var letter = $(this).data("letter");
        playLetter(letter);
        flash($(this));
    });

    // Physical keyboard support: press a letter that exists in this alphabet
    // and the matching button lights up + plays.
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
