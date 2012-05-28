$(function () {
    module("routes list tests", {
        setup: function () {
            var url1 = "/url1",
                url11 = "/url1/1",
                url12 = "/url1/2",
                url111 = "/url1/1/1",
                url2 = "/url2";
            $.router.routes.add(url1, 0);
            $.router.routes.add(url2, 0);
            $.router.routes.add(url11, 1);
            $.router.routes.add(url12, 1);
            $.router.routes.add(url111, 2);
        },
        teardown: function () {
            $.router.routes.clean(0);
        }
    }); 
    
    test('add test', function () { 
        console.log($.router.routes.list)
        equal($.router.routes.list.length, 3, "should contains 3 levels");
        equal($.router.routes.list[0].length, 2, "should contains 2 routes level 0");
        equal($.router.routes.list[1].length, 2, "should contains 2 routes level 1");
        equal($.router.routes.list[2].length, 1, "should contains 1 routes level 2");
    });
    
    test('clean test', function () {
        $.router.routes.clean(2);
        equal($.router.routes.list.length, 2, "should remove all routes level 2");
        $.router.routes.clean(1);
        equal($.router.routes.list.length, 1, "should remove all routes level 1");
    });

    test('clean all test', function () {
        $.router.routes.cleanAll();
        equal($.router.routes.list.length, 0, "should remove all routes");
    });
});
