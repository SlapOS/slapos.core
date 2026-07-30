(function () {
  "use strict";

  var messageElement = document.getElementById("message");
  var tbody = document.querySelector("#services tbody");

  function callJsonRpc(method, data) {
    // relative path so this works standalone or behind a reverse proxy
    // adding a path prefix (this page lives at .../henri/, the json-rpc
    // API lives one level up, at the root of the slapproxy application)
    return fetch("../" + method, {
      method: "POST",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data || {})
    }).then(function (response) {
      if (!response.ok) {
        return response.json().then(function (error) {
          throw new Error(error.title || response.statusText);
        });
      }
      return response.json();
    });
  }

  function setState(service, state) {
    messageElement.textContent = "";
    return callJsonRpc("slapos.post.v0.software_instance", {
      title: service.title,
      software_release_uri: service.software_release_uri,
      software_type: service.software_type,
      shared: service.shared,
      parameters: service.parameters,
      sla_parameters: service.sla_parameters,
      state: state
    }).then(loadServices, function (error) {
      messageElement.textContent = "Error: " + error.message;
    });
  }

  function renderServices(serviceList) {
    tbody.innerHTML = "";
    serviceList.forEach(function (service) {
      var row = document.createElement("tr");

      var titleCell = document.createElement("td");
      titleCell.textContent = service.title;
      row.appendChild(titleCell);

      var stateCell = document.createElement("td");
      stateCell.textContent = service.state;
      row.appendChild(stateCell);

      var actionCell = document.createElement("td");

      var startButton = document.createElement("button");
      startButton.type = "button";
      startButton.textContent = "Start";
      startButton.disabled = service.state === "started";
      startButton.addEventListener("click", function () {
        setState(service, "started");
      });
      actionCell.appendChild(startButton);

      var stopButton = document.createElement("button");
      stopButton.type = "button";
      stopButton.textContent = "Stop";
      stopButton.disabled = service.state === "stopped";
      stopButton.addEventListener("click", function () {
        setState(service, "stopped");
      });
      actionCell.appendChild(stopButton);

      row.appendChild(actionCell);
      tbody.appendChild(row);
    });
  }

  function loadServices() {
    return callJsonRpc("slapos.allDocs.WIP.instance_tree_list", {})
      .then(function (result) {
        return Promise.all(result.result_list.map(function (item) {
          return callJsonRpc("slapos.get.v0.software_instance", {
            instance_guid: item.instance_guid
          });
        }));
      })
      .then(renderServices, function (error) {
        messageElement.textContent = "Error: " + error.message;
      });
  }

  document.addEventListener("DOMContentLoaded", loadServices);
}());
