$(function () {
    module('routes list tests', {
        setup: function () {
            var url1 = '/url1',
                url11 = '/url1/1',
                url12 = '/url1/2',
                url111 = '/url1/1/1',
                url2 = '/url2';
            $.router.routes.add(url1, 0);
            $.router.routes.add(url2, 0);
            $.router.routes.add(url11, 1);
            $.router.routes.add(url12, 1);
            $.router.routes.add(url111, 2);
        },
        teardown: function () {
            $.router.routes.cleanAll();
        }
    }); 
    
    test('add tests', function () { 
        equal($.router.routes.list.length, 3, 'should contains 3 levels');
        equal($.router.routes.list[0].length, 2, 'should contains 2 routes level 0');
        equal($.router.routes.list[1].length, 2, 'should contains 2 routes level 1');
        equal($.router.routes.list[2].length, 1, 'should contains 1 routes level 2')
    });
    
    test('clean test', function () {
        $.router.routes.clean(2);
        equal($.router.routes.list.length, 2, 'should remove all routes level 2');
        $.router.routes.clean(1);
        equal($.router.routes.list.length, 1, 'should remove all routes level 1');
    });

    test('clean all test', function () {
        $.router.routes.cleanAll();
        equal($.router.routes.list.length, 0, 'should remove all routes');
    });

    module('search tests', {
        teardown: function () {
            $.router.routes.cleanAll();
        }
    });

    test('search test', function () {
        var url1 = {'route': '#/new/path', 'param1': 'foo1', 'param2': 'foo2', 'filter': true},
            url2 = {'route': '#/new/path/1', 'param1': 'foo1'},
            spy1 = sinon.spy(),
            spy2 = sinon.spy();
        console.log(url1);
        $.router.routes.add(url1.route, 0, spy1);
        $.router.routes.add('#/new/path/:id', 1, spy2);

        $.router.routes.search(url1);
        //delete url1.route;
        //ok(spy1.calledOnce);
        //ok(spy1.calledWith(url1));

        //$.router.routes.search(url2);
        //delete url2.route;
        //ok(spy2.calledOnce);
        //ok(spy2.calledWith(url2));
    });

    module('router methods tests', {
    });

    test('serialize tests', function () {
        deepEqual($.router.serialize({
            'param1': 'foo1',
            'param2': 'foo2',
            'filter': true
        }), 'param1=foo1&param2=foo2&filter=true');
    });
    
    test('deserialize tests', function () {
        deepEqual({
            'param1': 'foo1',
            'param2': 'foo2',
            'filter': true
        }, $.router.deserialize('param1=foo1&param2=foo2&filter=true'));
    });

    test('parseHash tests', function () {
        var response;
            urls = {
            '#/url1' : {'route': '/url1'},
            '#/url2?param1=foo1&param2=foo2': {'route': '/url2', 'param1': 'foo1', 'param2': 'foo2'},
            '#/url3?param1=foo1&param2=foo2&search': {'route': '/url3', 'param1': 'foo1', 'param2': 'foo2', 'search': true},
            '#/url4?&': {'route': '/url4'},
            '#/url5?param1=foo1&filter&row=4&redirect=/instance': {'route': '/url5', 'param1': 'foo1', 'filter': true, 'row': '4', 'redirect': '/instance'}
        };

        for (var url in urls) {
            response = $.router.parseHash(url);
            deepEqual(response, urls[url]);
        }
    });
});
