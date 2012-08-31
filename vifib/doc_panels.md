# How should be an html page using jquery mobile panel#

`
<html>
  <head>
  </head>
  <body>
    <!-- Anatomy of page using panels -->
     <div data-role="page">
       <!-- MENU -->
       <section data-role="panel" data-panel="menu">
         <header data-role="header">Menu</header>
         <nav>
          <ul data-role="listview">
            <li>List 1</li>
            <li>List 2</li>
            <li>List 3</li>
          </ul>
         </nav>
         <footer data-role="footer">Menu</footer>
       </section>
       <!-- LIST -->
       <section data-role="panel" data-panel="list">
         <header data-role="header">List 1</header>
         <nav>
          <ul data-role="listview">
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
          </ul>
         </nav>
         <footer data-role="footer">List 1</footer>
       </section>
       <!-- ITEM -->
       <section data-role="panel" data-panel="item">
         <header data-role="header">Item 1</header>
         <article>
         Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc rutrum lectus ut mauris ornare eu vestibulum arcu consectetur. Fusce massa elit, sollicitudin a iaculis at, accumsan sodales mi. Nulla ultrices placerat tellus, in lobortis lacus bibendum et. Ut mattis volutpat nunc ac auctor. Donec consequat venenatis facilisis. Vivamus metus leo, luctus faucibus vehicula rhoncus, placerat vitae ligula. Morbi sed risus ante, non sagittis augue. Nulla facilisi. Fusce vitae ipsum eget tortor cursus molestie. Etiam at nisl elit, vel dictum ipsum. In hac habitasse platea dictumst. In nisi metus, consequat id rutrum quis, rutrum sit amet leo.
         </article>
         <footer data-role="footer">Item 1</footer>
       </section>
     </div>
  </body>
</html>
`

# References #

## Examples ##

* [3 Column jQuery iPad Layout Bootstrap](http://www.jquery4u.com/demos/3-column-ipad-layout)
  [(demo)](http://www.jquery4u.com/demos/3-column-ipad-layout/)
* [JQM Multiview Plugin](https://github.com/frequent/multiview#readme)
  [(demo)](http://www.stokkers.mobi/jqm/multiview/demo.html)
* [Official widgets](https://github.com/jquery/jquery-mobile/tree/master/js/widgets)

## Howtos ##

* [Official Creating jQuery Mobile Plugins](https://github.com/jquery/jquery-mobile/wiki/Creating-jQuery-Mobile-Plugins)
* [Widget Factory](http://ajpiano.com/widgetfactory/)
