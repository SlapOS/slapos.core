// UTILS

$.fn.substractLists = function (l1, l2) {
    var newList = [];
    $.each(l2, function () {
        if ($.inArray(this.toString(), l1) === -1) {
            newList.push(this.toString());
        }
    });
    return newList;
};

/* Thanks to Ben Alman
 * https://raw.github.com/cowboy/jquery-misc/master/jquery.ba-serializeobject.js
 */
$.fn.serializeObject = function () {
    var obj = {};
    $.each(this.serializeArray(), function (i, o) {
        var n = o.name,
            v = o.value;
        obj[n] = obj[n] === undefined ? v
                : $.isArray(obj[n]) ? obj[n].concat(v)
                : [ obj[n], v ];
    });
    return obj;
};
