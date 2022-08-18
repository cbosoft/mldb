
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
    if (results_object.kind === "status_table") {
        display_status_table(results_object);
    }
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