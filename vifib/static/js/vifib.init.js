/**
 * NEXEDI
 * Author: Thomas Lechauve
 * Date: 6/28/12
 */
$(document).ready(function () {

    var appContext = $('body');

    //$.router.routes.add('/homepage', 0, appContext.vifib('showHomepage'));
    //$.router.routes.add('/library', 0, appContext.vifib('showLibrary'));
    //$.router.routes.add('/documentation', 0, appContext.vifib('showDocumentation'));
    $.router.routes.add('/dashboard', 0, appContext.vifib('showDashboard'));
    //$.router.routes.add('/instance', 0, appContext.vifib('showInstanceRoot'));
    //$.router.routes.add('/login', 0, appContext.vifib('showLogin'));

    appContext.slapos({'host': 'http://10.8.2.34:12006/erp5/portal_vifib_rest_api_v1'});
});
