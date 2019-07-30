from datetime import *
from .API_requester import *
from .Train import *
from pytz import timezone
import pytz
import time
import asyncio

# IDs of common train stations (to me)
# Probably should put this in a csv file somewhere

# Potential Idea for future:
# Everytime a station is searched, external CSV file is queried
# If cannot find then use API requesters. Then sort file
# so that a swfit binary search can be used and thus we don't need
# to use the API which may be slow and relies on a speedy internet
# connection which I don't have :(

strathfield_ID = '10101206'
parramatta_ID = '10101229'
central_ID = '10101100'
epping_ID = '10101429'

COMMON_STOPS = {
    'strathfield'  : strathfield_ID,
    'parramatta' : parramatta_ID,
    'central' : central_ID,
    'epping' : epping_ID
}

# Timezone stuff because the TFNSW API works in UTC time
syd_tz = timezone('Australia/Sydney')
# UTC time
utc = pytz.utc


class TrainSystem():
    def __init__(self):
        self._trains = []	


    ''' Return a list of train objects '''
    @property
    def trains(self):
        return self._trains	


    ''' Finds a list of the next 5 trains for a given timetable request.
        Input: Train_request object
        Return: a list of Train objects
    '''
    def find_me_trains(self, train_request):
        depart_from = train_request.departure_details
        arrive_at = train_request.arrival_details	
        # See if we can find a short cut (so far only for stra-cent)
        shortcut_reqs = []
        if ((depart_from == strathfield_ID) and
                (arrive_at == central_ID)):	
            shortcut_reqs = self._find_shortcut(train_request)

        # Generate train request for normal trains.
        # Convert time zones first
        if (train_request.depOrArrive == "dep"):
            train_request.times["Departure"] = \
                train_request.times["Departure"].astimezone(syd_tz)
        else:
            train_request.times["Arrival"] = \
                train_request.times["Arrival"].astimezone(syd_tz)

        # Make the requests asynchronously
        start = time.clock()
        reqs = shortcut_reqs + [train_request]
        r = Trip_requester().make_request1(reqs)

        # Interpret the requests (normal trains)
        normal_trains = self._interpret_trip_request(
            r[len(shortcut_reqs)], train_request, False)

        # Shortcut trains
        shortcut_trains = []
        for i, item in enumerate(shortcut_reqs):
            shortcut_trains = shortcut_trains + \
                self._interpret_trip_request(r[i], train_request, True)
        
        results = [x for x in normal_trains
                  if x not in shortcut_trains] + shortcut_trains

        # Sort
        # If we want to depart after then sort by departure time asc and
        # then sort by arrival time (in case of delays or what not)
        if (train_request.depOrArrive == "dep"):
            results.sort(key=lambda x: x.times["Departure"])
            results.sort(key=lambda x: x.times["Arrival"])
            print("these trains")
            for train in results:
                print(train.times["Departure"])
        # If we want to arrive before then sort by arrive time desc
        else:
            results.sort(key=lambda x: x.times["Arrival"], reverse=True)	
        # Truncate to 5 results
        del results[5:]	
        # store it in system
        self._trains = results
        return results


    ''' Given a stop name this finds its ID stored in the TFNSW system
        Input: Stop name string
        Return: List of tuples (name, ID, match quality)
    '''
    def find_stop(self, stop_name):
        if stop_name.lower() in COMMON_STOPS:
            return [(stop_name, COMMON_STOPS[stop_name.lower()])]
        # Get request
        r = StopFinder_requester().make_request(stop_name)
        # Try catch block in caller will catch HTTP errors and do smth
        # Get the results and filter out the ones that are train stops
        results_filtered = list(filter(
            lambda x: "productClasses" in x.keys() and
            1 in x["productClasses"] , r.json()["locations"]))	
        # Put results in a list
        matches = [(item["disassembledName"], item["id"], 
            item["matchQuality"]) for item in results_filtered]	
        # If there is multiple then sort by quality
        if len(matches) > 1:
            matches.sort(key= lambda x: x[2], reverse=True)	
        return matches	

        
    ''' If we are going strathfield to central, then this finds
        intercity trains that are 'setdown' only at strathfield
        Input: Train_request object
        Return: List of train_request objects 
    '''
    def _find_shortcut(self, train_request):
        # To minimise API requests (these bottleneck speed) we shall
        # search for trains from Epping/Parra -> Central and see if 
        # these trains stop at Strathfield.
        # All express trains going to Central must come from Epping or 
        # Parra
        if train_request.depOrArrive == "dep":
            # Epping/Parra -> Stra are both ~ 20 min on normal train
            # and ~ 12 on express. Therefore we use an offset of 25 min
            # and search for 10 trips from the API. We output 5 trips to 
            # the user so there will be enough overlap thus safe to use
            # this approximation	
            # This approximation will fail when there are major delays
            # but when there are major delays it is often a better idea
            # to just look at the announcements from the train ppl
            offset = 30
            dep_time = (train_request.times["Departure"] -
                        timedelta(minutes=offset)).astimezone(syd_tz)
            times = {"Departure": dep_time}
        else:
            arrival_time = \
                train_request.times["Arrival"].astimezone(syd_tz)
            times = {"Arrival": arrival_time}	
        # Epping to central
        epping_to_cent = Train_request(
            epping_ID, central_ID,
            times, Train_request.depOrArrive)
   
        # Parra to central trains
        parra_to_cent = Train_request(
            parramatta_ID, central_ID,
            times, Train_request.depOrArrive)

        return [epping_to_cent, parra_to_cent]
   
        '''
        # Make requests -> how about in parallel hm?
        r = Trip_requester().make_request(epping_to_cent)
        filtered_journeys1 = \
            self._interpret_trip_request(r, train_request, True)
        r = Trip_requester().make_request(parra_to_cent)
        filtered_journeys2 = \
            self._interpret_trip_request(r, train_request, True)

        # Put the two lists together (don't sort we do that later)
        filtered_journeys = filtered_journeys1 + filtered_journeys2
        return filtered_journeys
        '''


    ''' Extracts the data from the API request return into a format
        that is understandable.	
        Input: List of Dicts from API request, Train_request object
        Return: List of Trains with appropriate data
    '''
    def _interpret_trip_request(self, r, train_request, shortcut):
        if (shortcut):
            try:
                filtered_list = \
                    self._interpret_shortcut(r, train_request)
            except IndexError:
                filtered_list = []
        # No shortcut finding needed. Just make sure only trains
        else:
            filtered_list = list(filter(lambda x: "legs" in x.keys() and 
                len(x["legs"]) == 1 and "transportation" in x["legs"][0]
                and (x["legs"][0]["transportation"]["product"]
                    ["class"] == 1), r["journeys"]))	
        # Pull out info into a list of trains
        matches = []
        for item in filtered_list:
            journey = item["legs"][0]
            dest = journey["destination"]
            trip_id = (journey["transportation"]["properties"]
                ["tripCode"])
            line =journey["transportation"]["disassembledName"]
            if shortcut:
                b, dep = self._find_enroute(journey["stopSequence"]
                    ,strathfield_ID)
            else:
                dep = journey["origin"]	
            # Departure related info
            # For departure time, give precedence to real time
            # if no realtime data then use planned times
            dep, dep_time = \
                self._get_stop_details(dep, "departureTime")
            # bug fix
            if ((train_request.depOrArrive == "dep") and 
                (dep_time < train_request.times["Departure"])) :
                print("yeeting here")
                continue
            print("Found trains")
            print(dep)
            print(dep_time)
            print(train_request.times["Departure"])
            print("End found train")
            
            # Arrival related info
            dest, arr_time = \
                self._get_stop_details(dest, "arrivalTime") 
            newT = Train(dep, dest, {"Departure" : dep_time, 
                        "Arrival" : arr_time}, train_ID=trip_id, 
                        line=line)
            matches.append(newT)
        return matches


    ''' Extracts the data from the API request but does specific
        handling for shortcut routes
        Input: List of Dicts from API request, Train_request object
        Return: Filtered list of dicts
    '''
    def _interpret_shortcut(self, r, train_request):
        journey_list = r["journeys"]
        # Find the ones that are express trains and have stra enroute
        filtered_list = list(filter(lambda x: "legs" in x.keys() and 
			len(x["legs"]) == 1 and "transportation" in x["legs"][0]
			and x["legs"][0]["transportation"]["iconId"] == 2 and
            "stopSequence" in  x["legs"][0].keys() and 
            self._find_enroute(x["legs"][0]["stopSequence"],
            strathfield_ID), journey_list))

        # If we are departing from strathfield, also filter out ones
        # that are before our departure time
        # Find express trains that arrive at specified depart loc
        if (train_request.depOrArrive == "dep"):
            # Filter out times before intended departure time
            depart_at = train_request.times["Departure"]
            filtered_list = list(filter(lambda x: 
                self._get_departure_time(x["legs"][0]["stopSequence"],
                strathfield_ID) >= depart_at, filtered_list))	
            # Sort the times and find earliest departure from source
            filtered_list.sort(key= lambda x : 
                self._get_departure_time(x["legs"][0]["stopSequence"],
                    strathfield_ID))
        return filtered_list


    ''' Used to make a lambda fn less complicated by getting depart time
        from a stop enroute
        Input: Stop in stop sequence, stop_Id (string)
        Returns: Departure time from given stop_id for given journey
    '''
    def _get_departure_time(self, x, stop_ID):
        _, stop =  self._find_enroute(
            x, stop_ID)	
        stop, time =  self._get_stop_details(stop, "departureTime")
        return time	


    ''' Used to make a lambda fn less complicated in matching trip code
        Input: Journey list item, list of trip codes
        Returns: boolean
    '''
    def _match_trip_codes(self, x, filtered_list):
        toMatch = [item["legs"][0]["transportation"]["properties"]
            ["tripCode"] for item in filtered_list]	
        properties = x["legs"][0]["transportation"].get("properties")
        if (properties) and (properties.get("tripCode") in toMatch):
            return True
        else:
            return False


    ''' Given a stop it gets the arrive/depart time and the stop ID and 
        platform
        Input: Dict corresponding to a stop in json return, 
            String (either: 'arrivalTime' or 'departureTime')
        Return stop ID, DateTime
    '''
    def _get_stop_details(self, stop, timeString):
        if (stop.get(timeString+"Estimated")):
            time = stop.get(timeString+"Estimated")
        else:
            time = stop.get(timeString+"Planned")
        time = (utc.localize(datetime.strptime(time,
            "%Y-%m-%dT%H:%M:%Sz")).astimezone(syd_tz))
        stop = (stop["parent"]["id"], ''.join(x for x in 
            stop["name"] if x.isdigit()))	
        return stop, time


    ''' Finds if a given stop_id is enroute (the train stops) at that
        stop. If true then return true as well as the dict
        corresopnding to that stop
        Input: Dict corresponding to a stop in "stopSequence in
        json return, stop_id
        Return: Boolean, dict corresopnding to the stop
    '''
    def _find_enroute(self, stopSequence, stop_id):
        for item in stopSequence:
            if (item.get("parent").get("id") == stop_id and
                (item.get("departureTimePlanned") or
                 item.get("departureTimeEstimated"))):
                return True, item
        return False