function addLinksToDescriptions(link_marker) {
    $(".thing-description").each(function() {
        var raw_description = $(this).text();
        var new_description = "";

        var reading = false;
        var name = "";
        var replace_me = "*REPLACE_ME*";
        for (var i = 0; i < raw_description.length; i++) {
            if (raw_description[i] == link_marker) {
                if (reading) {
                    var link = "<a href=\"\/campaign\/thing/" + name + "\">" + name + "</a>";
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