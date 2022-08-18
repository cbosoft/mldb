function send_request(query)
{
    var xhr = new XMLHttpRequest();
    xhr.open("POST", window.location.href, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = () => { // Call a function when the state changes.
      if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
          console.log('response:')
          console.log(xhr.responseText);
        results_object = JSON.parse(xhr.responseText);
        display_result(results_object);
      }
    }
    xhr.send(JSON.stringify(query));
}


function hide_all()
{
    let elements = document.getElementsByClassName("container");
    for (let i = 0; i < elements.length; i++) {
        elements[i].style.display = "none";
    }
}

function display_about()
{
    hide_all()
    document.getElementById("about-container").style.display = "block";
}

function display_result(results_object)
{
    hide_all();
    if (results_object.hasOwnProperty("error")) {
        display_error(results_object);
    }
    if (results_object.kind === "status_table") {
        display_status_table(results_object);
    }
    else if (results_object.kind === "details") {
        display_exp_details(results_object);
    }

    if (results_object.hasOwnProperty("refresh")) {
        var query = results_object.refresh.query;
        var timeout = results_object.refresh.period;

        setTimeout(()=>{ send_request(query); }, timeout);
    }
}

function display_error(results_object)
{
    console.error(results_object.why);

    var container = document.getElementById("error-container");
    container.style.display = "block";
    var msg = document.getElementById("error-message");
    msg.innerText = results_object.why;

}

function display_status_table(results_object)
{
    var table_src = "<tr>";
    for (i in results_object.headings) {
        table_src += "<th>" + results_object.headings[i] + "</th>"
    }
    table_src += "</tr>";

    for (i in results_object.experiments) {
        table_src += "<tr>";
        table_src += "<td><a href='/index.html?show=details&expid=" + results_object.experiments[i] + "'>" + results_object.experiments[i] + "</a></td>";
        table_src += "<td>" + results_object.statuses[i] + "</td>";
        table_src += "</tr>";
    }

    // ensure the table of results is shown
    var container = document.getElementById("results-table-container");
    container.style.display = "block";

    // populate the table of results
    var res_table = document.getElementById("results-table");
    res_table.innerHTML = table_src;
    var ttle = document.getElementById("results-title");
    ttle.innerText = results_object.title;
}

function display_exp_details(results_object) {
    // ensure the table of results is shown
    var container = document.getElementById("experiment-details-container");
    container.style.display = "block";

    var ttle = document.getElementById("experiment-details-title");
    ttle.innerText = results_object.title;
    var details = results_object.details;

    var status_elem = document.getElementById("experiment-status");
    status_elem.innerHTML = details.status;

    var config_elem = document.getElementById("experiment-config");
    var params_def_html = "<dl>";
    for (i in results_object.params) {
        params_def_html += "<dt>" + i + "</dt><dd>" + results_object.params[i] + "</dd>";
    }
    params_def_html += "</dl>"
    config_elem.innerHTML = "<b><u>Params</u></b>" + params_def_html + "<b><u>Dataset</u></b><p>TODO</p>"

    var loss_canv = document.getElementById("experiment-loss-plot");
    var loss_err = document.getElementById("experiment-details-loss-plot-error");
    if (details.losses.hasOwnProperty('train')) {
        var train = [];
        for (i in details.losses.train.loss) {
            train.push({x: details.losses.train.epoch[i], y: details.losses.train.loss[i]})
        }
        var valid = [];
        for (i in details.losses.valid.loss) {
            valid.push({x: details.losses.valid.epoch[i], y: details.losses.valid.loss[i]})
        }

        loss_err.style.display = "none";
        loss_canv.style.display = "block";
        loss_plot(loss_canv, train, valid)

    }
    else {
        loss_err.style.display = "block";
        loss_canv.style.display = "none";
    }

}

var loss_chart = '';

function loss_plot(canv, train, valid)
{
    const ctx = canv.getContext("2d");

    if (!loss_chart) {
        loss_chart = new Chart(ctx, {
            type: 'scatter',
            options: {
                showLine: true,
                scales: {
                    xAxis: {
                        type: "logarithmic",
                        title: {
                            display: true,
                            text: "Epoch [#]"
                        }
                    },
                    yAxis: {
                        type: "logarithmic",
                        title: {
                            display: true,
                            text: "Loss"
                        }
                    },
                },
                elements: {
                    point: {
                        radius: 1.5
                    },
                    line: {
                        width: 1
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                var xy = context.parsed;
                                return 'Epoch: ' + xy.x + '// Loss: ' + xy.y;
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'x'
                },
                animation: {
                    duration: 0
                }
            }
        });
    }

    loss_chart.data = {
        datasets: [{
            label: 'Training Loss',
            data: train,
            backgroundColor: "steelblue",
            borderColor: "steelblue"
        }, {
            label: 'Valid Loss',
            data: valid,
            backgroundColor: "orange",
            borderColor: "orange"
        },]
    };
    loss_chart.update();
}


function metrics_plot(canv, metrics)
{
    const ctx = canv.getContext("2d");
    const chart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Training Loss',
                data: train,
                borderWidth: 1,
                backgroundColor: "steelblue"
            }, {
                label: 'Valid Loss',
                data: valid,
                borderWidth: 1,
                backgroundColor: "red"
            },]
        },
        options: {
            showLine: true,
            events: [],
            scales: {
                xAxis: {
                    type: "logarithmic",
                    title: {
                        display: true,
                        text: "Epoch [#]"
                    }
                },
                yAxis: {
                    type: "logarithmic",
                    title: {
                        display: true,
                        text: "Loss"
                    }
                },
            },
            elements: {
                point: {
                    radius: 1
                }
            }
        }
    });
}