function addLinksToDescriptions(thing_link_marker, thing_url, beyond_link_marker, beyond_url) {
    $(".thing-description, .encounter").each(function() {
        var raw_description = $(this).text();
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
