from bottle import *
from pathlib import Path

import utils
import calculation

app = Bottle()

@app.route("/")
def route__():
    redirect("/file/index.html")

@app.route("/file/<filepath:path>")
def route__file(filepath):
    return static_file(filepath, root = utils.get_project_dir() / "website" / "static")

@app.route("/do_lookup", method = "POST")
def route__do_lookup():
    begin_location_name = request.forms.get("begin_location")
    end_location_name = request.forms.get("end_location")
    begin_location_data = calculation.get_place_data(begin_location_name)
    end_location_data = calculation.get_place_data(end_location_name)
    field = calculation.form_url(
        "http://openstreetmap.org/directions",
        {
            "engine": "fossgis_osrm_foot",
            "route": "{0},{1};{2},{3}".format(
                begin_location_data["location"].latitude,
                begin_location_data["location"].longitude,
                end_location_data["location"].latitude,
                end_location_data["location"].longitude
            )
        }
    )
    route = calculation.get_route(
        begin_location_data["location"],
        end_location_data["location"]
    )
    path_covid_results = calculation.get_path_covid_results(route)
    table_template_file = open(
        utils.get_project_dir() / "website" / "templates" / "table.html"
    )
    table_template = SimpleTemplate(table_template_file.read())
    table_template_file.close()
    print(path_covid_results["travel"]["places_with_most_covid"])
    table_template_rendered = table_template.render({
        "field": field,
        "tpc": path_covid_results["travel"]["total_people_contact"],
        "wtpc": path_covid_results["travel"]["weighted_total_people_contact"],
        "mcc": path_covid_results["travel"]["places_with_most_covid"]
    })
    return table_template_rendered

host = input("Host: ")
port = input("Port: ")

app.run(host = host, port = port)
