$.vifib.panel = {
    carousel:
        '<article id="slider">' +
        '<ul>' +
        '<li style="display: block">' +
        '<h2>Paas Without limit</h2>' +
        '<p>c c++ java javascript perl php python</p><p>kumofs mysql mariadb memcached</p><p>apache nodejs flask tomcat zope</p>' +
        '</li>' +
        '<li style="display: none">' +
        '<h2>Iaas broker</h2>' +
        '<p>xen kvm hyperv vmware openstack</p><p>opennebula amazon eucalyptus</p><p> niftyname gandi rackspace</p>' +
        '</li>' +
        '<li style="display: none">' +
        '<h2>Resilient Cloud Computing</h2>' +
        '<fieldset class="ui-grid-a">' +
        '<div class="ui-block-a">' +
        '<ul>' +
        '<li>decentralized</li>' +
        '<li>open-source</li>' +
        '</ul>' +
        '</div>' +
        '<div class="ui-block-b">' +
        '<ul>' +
        '<li>10x cost efficient</li>' +
        '<li>tremendously simpler</li>' +
        '</ul>' +
        '</div>' +
        '</fieldset>' +
        '</li>' +
        '<li style="display: none">' +
        '<h2>Mobile Edge Computing</h2>' +
        '<p>bsd linux macos windows android tizen</p>' +
        '</li>' +
        '<li style="display: none">' +
        '<h2>Billing</h2>' +
        '<p>accoutning billing charging crm portal market</p>' +
        '</li>' +
        '<li style="display: none">' +
        '<h2>Saas for free</h2>' +
        '<p>wordpress drupal erp5 prestashop joomla</p><p>xwiki mediawiki oscommerce sugarcrm</p><p>phpbb facturalux zabbix</p>' +
        '</li>' +
        '</ul>' +
        '</article>',
        
    simplelist:
        '<article>' +
        '<ul data-role="listview">' +
        '{{# links }}' +
        '<li><a href="{{ url }}">{{ name }}</a></li>' +
        '{{/ links }}' +
        '</ul>' +
        '</article>',
    failed:
        '<article>' +
        '<center><h4>This page does not exist</h4></center>' +
        '</article>',
    blank:
        '<article></article>',
    login:
        '<article>' +
        '<h2>Sign in with</h2>' +
        '<a data-role="button" href="#/login/facebook">Facebook</a><br/>' +
        '<a data-role="button" href="#/login/google">Google</a>' +
        '</article>',
    sidemenu: {
        main: '<aside><nav><ul data-role="listview">{{# links }}<li><a href="{{ url }}">{{ name }}</a></li>{{/ links }}</ul></nav></aside>',
        library:
            '<aside><nav>' +
            '<ul data-role="listview" data-theme="d">' +
            '{{# links }}' +
            '<li><a href="{{ url }}">{{ name }}</a></li>' +
            '{{/ links }}' +
            '<li data-role="divider">Categories</li>' +
            '{{# categories }}' +
            '<li><a href="{{ url }}">{{ name }}</a></li>' +
            '{{/ categories }}' +
            '</ul></nav></aside>'
    },
    categories:
        '<article><ul data-role="listview"><li data-role="divider">Categories</li>{{# categories }}<li><a href="{{ url }}">{{ name }}</a></li>{{/ categories }}</ul></article>',
    library:
        '<article>' +
             '<form id="search-library">' +
                '<div data-role="fieldcontain" class="ui-hide-label">' +
                    '<label for="search"></label>' +
                    '<input type="search" name="search" placeholder="Search"/>' +
                '</div>' +
             '</form>' +
            '<ul data-role="listview" data-inset="true">' +
                '<li data-role="list-divider">Most downloaded</li>' +
                '{{# most }}' +
                '<li><a href="{{ url }}"><h4>{{ name }}</h4></a></li>' +
                '{{/ most }}' +
                '<li data-role="list-divider">Brand new</li>' +
                '{{# newest }}' +
                '<li><a href="{{ url }}"><h4>{{ name }}</h4></a></li>' +
                '{{/ newest }}' +
        '</ul></article>',
    software:
        '<article>' +
        '<img src="{{ image_url }}">' +
        '<p><b>{{ description }}</b></p>' +
        '<a data-role="button" href="#/login">Buy it for {{ price }}&euro;</a>' +
        '</article>',
    allsoftware:
        '<article>' +
        '<ul data-role="listview">' +
        '</ul>' +
        '</article>',
    rowsoftware:
        '<a href="{{ softurl }}">' +
        '{{# thumb_url }}' +
        '<img src="{{ thumb_url }}">'+
        '{{/ thumb_url }}' +
        '<h3>{{ name }}</h3>' +
        '</a>',
    instancerequest:
        '<article>' +
        '<form id="instancerequest">' +
        '<div data-role="fieldcontain">' +
        '<label for="title" class="ui-input-text">Title:</label>' +
        '<input type="text" name="title" required/>' +
        '</div>' +
        '<div data-role="fieldcontain">' +
        '<label for="software_release" class="ui-input-text">Software release:</label>' +
        '<input type="text" name="software_release" value="http://example.com/example.cfg"/>' +
        '</div>' +
        '<button value="Submit" type="submit">Submit</button>' +
        '</form>' +
        '</article>',
    instance:
        '<article>' +
        '<center><h3>{{ title }}</h3></center>' +
        '<ul data-role="listview">' +
        '<li class="ui-li-static">' +
        '<p class="ui-li-desc"><i>Software release</i></p>' +
        '<h3 class="ui-li-heading"><a href="{{ software_release }}">{{ software_release }}</a></h3>' +
        '</li>' +
        '<li class="ui-li-static">' +
        '<p class="ui-li-desc"><i>Software type</i></p>' +
        '<h3 class="ui-li-heading">{{ software_type }}</h3>' +
        '</li>' +
        '<li class="ui-li-static">' +
        '<p class="ui-li-desc"><i>Status</i></p>' +
        '<h3 class="ui-li-heading">{{ status }}</h3>' +
        '</li>' +
        '</ul>' +
        '{{# start_requested }}' +
        '<a data-role="button" href="{{ stop_url }}">Stop</a>' +
        '<a data-role="button" href="{{ destroy_url }}">Destroy</a>' +
        '{{/ start_requested }}' +
        '{{# stop_requested }}' +
        '<a data-role="button" href="{{ start_url }}">Start</a>' +
        '<a data-role="button" href="{{ destroy_url }}">Destroy</a>' +
        '{{/ stop_requested }}' +
        '' +
        '</article>',
    instancelist:
        '<article>' +
        '<a href="#/dashboard/instance/request" data-role="button">Create a new instance</a>' +
        '<ul data-role="listview">' +
        '</ul>' +
        '</article>',
    rowinstance:
        '<a href="{{ insturl }}">{{ title }}</a>',
    computer:
        '<article>' +
        '<h2>{{ computer_id }}</h2>' +
        '</article>',
    allcomputer:
        '<article>' +
        '<ul data-role="listview">' +
        '</ul>' +
        '</article>',
    rowcomputer:
        '<a href="{{ compurl }}">' +
        '{{ computer_id }}' +
        '</a>',
    notfound:
        '<article>' +
        '<center><h4>This resource could not be found</h4></center>' +
        '</article>',
    badrequest:
        '<article>' +
        '<center><h4>Something went wrong, the server receive an incorrect request</h4></center>' +
        '</article>',
    payment:
        '<article>' +
        '<center><h4>Your account is locked because of non payment/h4></center>' +
        '</article>',
    internalerror:
        '<article>' +
        '<center><h4>This resource could not be found</h4></center>' +
        '</article>',
    nosoftware:
        '<article>' +
        '<h4>The software you are looking for, named "{{ name }}", does not exist</h4>' +
        '</article>',
    noinstance:
        '<article>' +
        '<h4>The instance you are looking for, named "{{ name }}", does not exist</h4>' +
        '</article>',
    nocomputer:
        '<article>' +
        '<h4>The computer you are looking for, named "{{ name }}", does not exist</h4>' +
        '</article>',
}

$.vifib.header = {
  default: '<header data-role="header"><a href="#" data-icon="home" data-iconpos="notext"></a><h2>{{ title }}</h2></div></header><div id="loading" style="position: absolute; top: 20px; right: 20px;"></div>'
}

$.vifib.footer = {
        overview: '<footer data-role="footer"><div data-role="navbar"><ul><li><a href="#/library/">Library</a></li><li><a href="http://packages.python.org/slapos.core/">Documentation</a></li></ul></div></footer>'
}
