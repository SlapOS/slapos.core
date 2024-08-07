/*jslint indent: 2, maxlen: 80, nomen: true */
/*global console, window, document, RSVP, XMLHttpRequest */
(function (document, RSVP, XMLHttpRequest) {
  "use strict";
  var promise_list = [],
    relative_url_path = "/app",
    test_url_list = [
      { name : 'Europe 1',
        testurl: "https://demoapp-eu1.erp5.cn/WebSite_getTestFrontendResponse",
        redirect: "https://demoapp-eu1.erp5.cn" + relative_url_path },
      { name : 'Europe 2',
        testurl: "https://demoapp-eu1.erp5.cn/WebSite_getTestFrontendResponse",
        redirect: "https://demoapp-eu2.erp5.cn" + relative_url_path },
      { name : 'North America 1',
        testurl: "https://demoapp-na1.erp5.cn/WebSite_getTestFrontendResponse",
        redirect: "https://demoapp-na1.erp5.cn" + relative_url_path },
      { name : 'North America 2',
        testurl: "https://demoapp-na2.erp5.cn/WebSite_getTestFrontendResponse",
        redirect: "https://demoapp-na2.erp5.cn" + relative_url_path },
      { name : 'China CT',
        testurl: "https://demoapp-ct1.erp5.cn/WebSite_getTestFrontendResponse",
        redirect: "https://demoapp-ct1.erp5.cn" + relative_url_path },
      { name : 'China CU',
        testurl: "https://demoapp-cu1.erp5.cn/WebSite_getTestFrontendResponse",
        redirect: "https://demoapp-cu1.erp5.cn" + relative_url_path },
      { name : 'China CM',
        testurl: "https://demoapp-cm1.erp5.cn/WebSite_getTestFrontendResponse",
        redirect: "https://demoapp-cm1.erp5.cn" + relative_url_path },
      { name : 'Asia 1',
        testurl: "https://demoapp-as1.erp5.cn/WebSite_getTestFrontendResponse",
        redirect: "https://demoapp-as1.erp5.cn" + relative_url_path },
      { name : 'Asia 2',
        testurl: "https://demoapp-as2.erp5.cn/WebSite_getTestFrontendResponse",
        redirect: "https://demoapp-as2.erp5.cn" + relative_url_path }
    ];

  function ajax(param) {
    var xhr = new XMLHttpRequest();
    return new RSVP.Promise(function (resolve, reject, notify) {
      var k;
      xhr.open(param.type || "GET", param.url, true);
      xhr.responseType = param.dataType || "";
      if (typeof param.headers === 'object' && param.headers !== null) {
        for (k in param.headers) {
          if (param.headers.hasOwnProperty(k)) {
            xhr.setRequestHeader(k, param.headers[k]);
          }
        }
      }
      xhr.addEventListener("load", function (e) {
        if (e.target.status >= 400) {
          return reject(e);
        }
        return resolve(e);
      });
      xhr.addEventListener("error", reject);
      xhr.addEventListener("progress", notify);
      if (typeof param.xhrFields === 'object' && param.xhrFields !== null) {
        for (k in param.xhrFields) {
          if (param.xhrFields.hasOwnProperty(k)) {
            xhr[k] = param.xhrFields[k];
          }
        }
      }
      if (typeof param.beforeSend === 'function') {
        param.beforeSend(xhr);
      }
      xhr.send(param.data);
    }, function () {
      xhr.abort();
    });
  }
  function testURL(url) {
    return RSVP.Queue()
      .push(function () {
        return ajax({
          url: url
        });
      })
      .push(function (evt) {
        return evt.target.responseText;
      }, function () {
        return "FAIL";
      });
  }

  function launchTest(test_case) {
    var start = new Date().getTime(),
      url = test_case.testurl;
    return new RSVP.Queue()
      .push(function () {
        return RSVP.any([RSVP.delay(4000),
          testURL(url + "?nocache=" + start)]);
      })
      .push(function (result) {
        var elapsed = new Date().getTime() - start;
        if (result === undefined) {
          return {url: test_case.redirect,
            time: 1000000001,
            name: test_case.name};
        }
        if (result === "FAIL") {
          return {url: test_case.redirect,
            time: 1000000000,
            name: test_case.name};
        }
        return {url: test_case.redirect,
          name: test_case.name,
          time: elapsed};
      });
  }

  function runOnce(test_queue) {
    return new RSVP.Queue()
      .push(function () {
        var u;
        for (u in test_url_list) {
          if (test_url_list.hasOwnProperty(u)) {
            test_queue.push(launchTest(test_url_list[u]));
          }
        }
        return RSVP.all(test_queue);
      })
      .push(undefined, function (reason) {
        console.log(reason);
        return "OK";
      });
  }

  function renderPartialResult(result, main_div, winner_div) {
    var u, y, interaction, winner = 0,
      t_i, table_dict = {}, interaction_dict = {}, msg = "";

    msg += "<table width=100%>";

    for (u in result) {
      if (result.hasOwnProperty(u)) {
        interaction = parseInt(u / test_url_list.length, 10);

        if (!interaction_dict.hasOwnProperty(interaction)) {
          interaction_dict[interaction] = 1;
        }
        if (!table_dict.hasOwnProperty(result[u].name)) {
          table_dict[result[u].name] = {
            total: 0,
            name: result[u].name,
            url: result[u].url
          };
        }
        if (result[u].time === 1000000000) {
          table_dict[result[u].name][interaction] = "FAIL";
          table_dict[result[u].name].total = "REJECT";
        } else  if (result[u].time === 1000000001) {
          table_dict[result[u].name][interaction] = "TIMEOUT";
          table_dict[result[u].name].total = "REJECT";
        } else {
          table_dict[result[u].name][interaction] = result[u].time;
          if (table_dict[result[u].name].total !== "REJECT") {
            table_dict[result[u].name].total += result[u].time;
          }
        }
      }
    }
    msg += "</tr> <th> </th>";
    t_i = 0;
    for (u in interaction_dict) {
      if (interaction_dict.hasOwnProperty(u)) {
        msg += '<th> Test ' + u + "</th>";
        t_i += 1;
      }
    }
    msg += "<th class='avg'> AVERAGE </th></tr>";

    for (u in table_dict) {
      if (table_dict.hasOwnProperty(u)) {
        if (winner === 0) {
          winner = table_dict[u];
        }
        if (table_dict[u].total !== "REJECT") {
          table_dict[u].average = table_dict[u].total / t_i;
          if (winner.average === "REJECT") {
            winner = table_dict[u];
          }
          if (winner.average > table_dict[u].average) {
            winner = table_dict[u];
          }
        } else {
          table_dict[u].average = "REJECT";
        }
      }
    }


    for (u in table_dict) {
      if (table_dict.hasOwnProperty(u)) {
        if (u === winner.name) {
          msg += "<tr class='winner'>";
        } else {
          msg += "<tr>";
        }
        msg += '<td><a href="' + table_dict[u].url + '">' + u + '</a></td>';
        for (y in interaction_dict) {
          if (interaction_dict.hasOwnProperty(y)) {
            msg += "<td>" + table_dict[u][y] + "</td>";
          }
        }
        msg += "<td>" + table_dict[u].average + "</td>";
        msg += "</tr>";
      }
    }

    msg += "</table>";

    msg = "<h2> The best frontend for you is ... <strong>" +
      winner.name + " </strong> </h2>" + msg;

    main_div.innerHTML = msg;

    msg = "";
    msg += "<p><a class=btn href=" + winner.url + "> Click to Connect via ";
    msg +=  winner.name + "</a> </p>";

    winner_div.innerHTML = msg;
    return winner;
  }

  function runAll() {
    return runOnce(promise_list)
      .push(function () {
        return runOnce(promise_list)
          .push(function () {
            return runOnce(promise_list)
              .push(function () {
                return runOnce(promise_list)
                  .push(function () {
                    return runOnce(promise_list)
                      .push(function (result) {
                        var winner,
                          div = document.getElementsByClassName("table"),
                          winner_div = document.getElementsByClassName("link");

                        winner = renderPartialResult(result,
                          div[0],
                          winner_div[0]);

                        return winner;
                      });
                  });
              });
          });
      });
  }

  runAll();

}(document, RSVP, XMLHttpRequest));