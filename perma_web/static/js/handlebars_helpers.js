Handlebars.registerHelper ('truncatechars', function (str, len) {
    if (str.length > len) {
        var new_str = str.substr (0, len+1);

        while (new_str.length) {
            var ch = new_str.substr ( -1 );
            new_str = new_str.substr ( 0, -1 );
            if (ch == ' ') break;
        }

        if ( new_str == '' ) new_str = str.substr ( 0, len );

        return new Handlebars.SafeString ( new_str +'...' ); 
    }
    return str;
});
