function addLinksToDescriptions(thing_link_marker, thing_url, beyond_link_marker, beyond_url, item_link_marker, item_url, spell_link_marker, spell_url) {
    $(".thing-description, .encounter, .random_attribute").each(function() {
        var raw_description = "<p>" + $(this).text()
            .replace(/\n{2}/g, "</p><p>")
            .replace(/\*-/g, "<ul>")
            .replace(/-\*/g, "</ul>")
            .replace(/- /g, "<li>")
            .replace(/-\n/g, "</li>")
            + "</p>";
        var new_description = "";

        var reading = false;
        var name = "";
        var replace_me = "*REPLACE_ME*";
        for (var i = 0; i < raw_description.length; i++) {
            if (raw_description[i] == thing_link_marker) {
                if (reading) {
                    var link = "<a class=\"thing\" href=\"" + thing_url + name + "\">" + name + "</a>";
                    new_description = new_description.replace(replace_me, link);
                    console.log("Replaced " + name + " with " + link);
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
                    var link = "<a class=\"monster\" href=\"" + beyond_url + name.replace(/ /g, '-') + "\" target=\"_blank\">" + name + "</a>";
                    new_description = new_description.replace(replace_me, link);
                    console.log("Replaced " + name + " with " + link);
                    name = '';
                    reading = false;
                }
                else {
                    new_description += replace_me;
                    reading = true;
                }
            }
            else if (raw_description[i] == item_link_marker) {
                if (reading) {
                    var link = "<a class=\"item\" href=\"" + item_url + name.replace(/ /g, '-') + "\" target=\"_blank\">" + name + "</a>";
                    new_description = new_description.replace(replace_me, link);
                    console.log("Replaced " + name + " with " + link);
                    name = '';
                    reading = false;
                }
                else {
                    new_description += replace_me;
                    reading = true;
                }
            }
            else if (raw_description[i] == spell_link_marker) {
                if (reading) {
                    var link = "<a class=\"spell\" href=\"" + spell_url + name.replace(/ /g, '-') + "\" target=\"_blank\">" + name + "</a>";
                    new_description = new_description.replace(replace_me, link);
                    console.log("Replaced " + name + " with " + link);
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

function getRandomAttribute(attribute, url, callbackFunction) {
    $.getJSON(url, {}, callbackFunction);
}
