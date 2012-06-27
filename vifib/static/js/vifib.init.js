/**
 * NEXEDI
 * Author: Thomas Lechauve
 * Date: 6/28/12
 */
$(document).ready(function () {

    var appContext = $('body');

    $.router.routes.add('/homepage', 0, methods.showHomepage, appContext);
    $.router.routes.add('/library', 0, methods.showLibrary, appContext);
    $.router.routes.add('/documentation', 0, methods.showDocumentation, appContext);
    $.router.routes.add('/dashboard', 0, methods.showDashboard, appContext);
    $.router.routes.add('/instance', 0, methods.showInstanceRoot, appContext);
    $.router.routes.add('/login', 0, methods.showLogin, appContext);

    appContext.slapos({'host': 'http://10.8.2.34:12006/erp5/portal_vifib_rest_api_v1'});
});
