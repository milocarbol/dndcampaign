function addLinksToDescriptions(thing_link_marker, thing_url, beyond_link_marker, beyond_url) {
    $(".thing-description, .encounter").each(function() {
        var raw_description = $(this).text()
            .replace(/\*-/g, "<ul>")
            .replace(/-\*/g, "</ul>")
            .replace(/- /g, "<li>")
            .replace(/-\n/g, "</li>");
        var new_description = "";

        var reading = false;
        var name = "";
        var replace_me = "*REPLACE_ME*";
        for (var i = 0; i < raw_description.length; i++) {
            if (raw_description[i] == thing_link_marker) {
                if (reading) {
                    var link = "<a href=\"" + thing_url + name + "\">" + name + "</a>";
                    new_description = new_description.replace(replace_me, link);
                    name = '';
                    reading = false;
                }
                else {
                    new_description += replace_me;
                    reading = true;
                }
            }
            else if (raw_description[i] == beyond_link_marker) {
                if (reading) {
                    var link = "<a href=\"" + beyond_url + name.replace(' ', '-') + "\" target=\"_blank\">" + name + "</a>";
                    new_description = new_description.replace(replace_me, link);
                    name = '';
                    reading = false;
                }
                else {
                    new_description += replace_me;
                    reading = true;
                }
            }
            else if (reading) {
                name += raw_description[i];
            }
            else {
                new_description += raw_description[i];
            }
        }
        $(this).html(new_description);
    })
}
function evaluateFilters() {
    if ($(".thing-filter.active").length == 0) {
        $(".thing-block").show();
    }
    else {
        $(".thing-block").hide();
        if ($("#match-button").hasClass("match-by-or")) {
            $(".thing-filter.active").each(function() {
                var clss = $(this).attr("id");
                $(".thing-block." + clss).show();
            });
        }
        else {
            var clsses = "";
            $(".thing-filter.active").each(function() {
                clsses += "." + $(this).attr("id");
            });
            $(".thing-block" + clsses).show();
        }
    }
}
