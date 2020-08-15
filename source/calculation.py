import utils
import urllib.request
import json
import html.parser
import re

from codecs import BOM_UTF8

class Location:
    def __init__(self, i_longitude, i_latitude):
        self.longitude = i_longitude
        self.latitude = i_latitude

    def __repr__(self):
        return "Location(" + self.longitude + ", " + self.latitude + ")"

class Geopath:
    def __init__(self, i_begin_location, i_end_location, i_distance, i_duration, i_parts):
        self.begin_location = i_begin_location
        self.end_location = i_end_location
        self.distance = i_distance
        self.duration = i_duration
        self.parts = i_parts

class GeopathPart:
    def __init__(
            self,
            i_mode_of_travel,
            i_location1,
            i_location2,
            i_distance,
            i_duration
        ):
        self.mode_of_travel = i_mode_of_travel
        self.location1 = i_location1
        self.location2 = i_location2
        self.distance = i_distance
        self.duration = i_duration

def strip_bom(b):
    if b[:len(BOM_UTF8)] == BOM_UTF8:
        return b[len(BOM_UTF8):]
    else:
        return b

def get_web_resource(url):
    header_options = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"}
    url_request = urllib.request.Request(url, None, header_options)
    return strip_bom(urllib.request.urlopen(url_request).read()).decode("utf-8")

def form_url(url_base, options):
    return url_base + "?" + urllib.parse.urlencode(options)

def str_match(s1, s2):
    return s1.lower() == s2.lower()
    
def get_api_key():
    return open(utils.get_project_dir() / "google_maps_api_key.txt").read().strip()

def get_place_data(place_name):
    url_base = "http://openstreetmap.org/geocoder/search_osm_nominatim"
    url = form_url(
        url_base,
        {
            "query": place_name
        }
    )

    print(url)

    response = get_web_resource(url)
    print(response)

    class StreamingHTMLParser(html.parser.HTMLParser):
        def __init__(self):
            html.parser.HTMLParser.__init__(self)
            self.data = None
            self.data_found = False

        def handle_starttag(self, tag_name, attributes):
            if self.data_found:
                return
            attributes_d = dict(attributes)
            if tag_name == "li":
                if self.data is None:
                    self.data = dict()
            if tag_name == "a" and "data-lat" in attributes_d:
                self.data["location"] = Location(attributes_d["data-lon"], attributes_d["data-lat"])
                self.data_found = True

        def handle_data(self, chars):
            if self.data_found:
                return
            if self.data is not None:
                if "location" not in self.data:
                    self.data["usage"] = chars[:-1]

    parser = StreamingHTMLParser()
    parser.feed(response)
    parser.close()

    return parser.data

def get_covid_case_fraction(county_name, state_name):
    response = get_web_resource("http://cdc.gov/coronavirus/2019-ncov/json/county-map-data.json")
    response_data = json.loads(response)
    for entry in response_data["data"]:
        if str_match(entry["state"], state_name) and str_match(entry["county_name"], county_name):
            return int(entry["rate_per_100k"]) / 100000

def get_route(location1, location2):
    print(location1, location2)
    url_base = "http://routing.openstreetmap.de/routed-foot/route/v1/driving/"
    url_base += "{0},{1};{2},{3}".format(
        location1.longitude,
        location1.latitude,
        location2.longitude,
        location2.latitude
    )
    print(url_base)
    options = {
        "overview": "false",
        "geometries": "polyline",
        "steps": "true"
    }
    url = form_url(url_base, options)
    print(url)
    response = get_web_resource(url)
    response_data = json.loads(response)["routes"][0]
    total_distance = response_data["distance"]
    total_duration = response_data["duration"]
    parts = []
    past_location = location1
    for leg in response_data["legs"]:
        for step in leg["steps"]:
            distance = step["distance"]
            duration = step["duration"]
            location = Location(
                step["maneuver"]["location"][0],
                step["maneuver"]["location"][1]
            )
            parts.append(GeopathPart(
                "walking",
                past_location,
                location,
                distance,
                duration
            ))
    return Geopath(location1, location2, total_distance, total_duration, parts)

def get_county(location):
    state_file = open(utils.get_project_dir() / "state_file.txt", "r")
    state_long_names_to_names = json.loads(state_file.read())
    state_file.close()
    
    url_base = "http://www.openstreetmap.org/geocoder/search_osm_nominatim_reverse"
    url = form_url(
        url_base,
        {
            "lat": location.latitude,
            "lon": location.longitude,
            "zoom": 17,
            "minlon": -122,
            "minlat": 47,
            "maxlon": -121,
            "maxlat": 48
        }
    )

    print(url)

    response = get_web_resource(url)
    print(response)

    class StreamingHTMLParser(html.parser.HTMLParser):
        def __init__(self):
            html.parser.HTMLParser.__init__(self)
            self.data = None

        def handle_starttag(self, tag_name, attributes):
            attributes_d = dict(attributes)
            if tag_name == "a" and "data-name" in attributes_d:
                self.data = attributes_d["data-name"]

    parser = StreamingHTMLParser()
    parser.feed(response)
    parser.close()
    
    match = re.search("(\w* County), ([^,]*)", parser.data)
    county_name = match.group(1)
    state_long_name = match.group(2)
    state_name = state_long_names_to_names[state_long_name]
    return (county_name, state_name)

def get_path_covid_results(path):
    mode_factors = {
        "walking": 1/60
    }
    
    results = {}
    results["travel"] = {}
    results["travel"]["total_distance"] = path.distance
    results["travel"]["total_duration"] = path.duration

    total_people_contact = 0
    weighted_total_people_contact = 0
    counties_and_covid_rates = {}
    for part in path.parts:
        mode = part.mode_of_travel
        loc2 = part.location2
        county, state = get_county(loc2)

        covid_rate = get_covid_case_fraction(county, state)
        mode_factor = mode_factors[mode]
        duration = part.duration

        counties_and_covid_rates[(county, state)] = covid_rate

        people_contact = mode_factor * duration
        weighted_people_contact = covid_rate * mode_factor * duration
        total_people_contact += people_contact
        weighted_total_people_contact += weighted_people_contact

    results["travel"]["total_people_contact"] = total_people_contact
    results["travel"]["weighted_total_people_contact"] = weighted_total_people_contact
    print(counties_and_covid_rates)
    counties_and_covid_rates = list(counties_and_covid_rates)
    print(counties_and_covid_rates)
    counties_and_covid_rates.sort(key = lambda a: a[1])
    print(counties_and_covid_rates)
    places_with_most_covid = list(counties_and_covid_rates)
    results["travel"]["places_with_most_covid"] = places_with_most_covid

    return results
