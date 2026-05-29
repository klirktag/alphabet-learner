$(function () {
    // Pre-load one Audio object per letter so playback is instant on tap.
    var sounds = {};
    $(".key").each(function () {
        var letter = $(this).data("letter");
        var audio = new Audio("sound/" + letter + ".mp4");
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
    $("#keyboard").on("pointerdown", ".key", function (e) {
        e.preventDefault();
        var letter = $(this).data("letter");
        playLetter(letter);
        flash($(this));
    });

    // Physical keyboard support: pressing A–Z triggers the same key.
    $(document).on("keydown", function (e) {
        if (e.repeat) return;
        var key = (e.key || "").toLowerCase();
        if (key.length !== 1 || key < "a" || key > "z") return;
        var $btn = $('.key[data-letter="' + key + '"]');
        if (!$btn.length) return;
        playLetter(key);
        flash($btn);
    });
});
