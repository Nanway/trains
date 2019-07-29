from flask import render_template, request, redirect, Markup, url_for
from server import app, system
from datetime import *
from src.Train import *
from src.TrainSystem import syd_tz, utc, timezone, pytz

@app.route('/', methods=['POST', 'GET'])
def home():
    data = request.form
    if request.method == 'POST':
        # Get departure station either selected in radio button 
        # or typed in
        if (data["Departure Station"] == ''):
            if (data.get("depart_radio")):
                depart_station = normalise(data.
                    get("depart_radio"))
            else:
                return render_template('home.html', err=
                    "Did you leave departures blank?")
        else:
            try:
                depart_station = system.find_stop(data
                    ["Departure Station"])
            except:
                return render_template('home.html', err=
                    "Oops something happened when finding departures")

        # Same but for arrivals
        if (data["Arrival Station"] == ''):
            if (data.get("depart_radio")):
                arrival_station = normalise(data.
                    get("arrive_radio"))
            else:
                return render_template('home.html', err=
                    "Did you leave arrivals blank?")
        else:
            try:
                arrival_station = system.find_stop(data
                    ["Arrival Station"])
            except:
                return render_template('home.html', err=
                    "Oops something happened when finding arrivals")

        # No stops found then give an error
        if (len(depart_station) == 0):
            return render_template('home.html', 
                err="Couldn't find departure station")
        elif(len(arrival_station) == 0):
            return render_template('home.html',
                err="Couldn't find arrival station")

        depart_id = depart_station[0][1]
        arrive_id = arrival_station[0][1]
        # Convert time to UTC date time format
        time = datetime.strptime(data["Input Time"], "%H:%M")
        req_time = datetime.now().replace(hour=time.hour,
            minute=time.minute, second=0, microsecond=0)
        req_time = syd_tz.localize(req_time)
        req_time = req_time.astimezone(utc)

        depOrArr = data["DepOrArr"]
        if (depOrArr == "dep"):
            times = {"Departure" : req_time}
        elif (depOrArr == "arr"):
            times = {"Arrival" : req_time}

        train_req = Train_request(depart_id, arrive_id, times, depOrArr)

        try:
            trains = system.find_me_trains(train_req)
        except IndexError:
            return_data = {"depart_station" : depart_station,
                "arrive_station" : arrival_station,
                "train_list" : [], "time" : data["Input Time"],
                "depOrArr" : data["DepOrArr"]}
            return render_template('home.html',
                err="No trains found", return_data=return_data)
        except Exception as e:
            e = "Something went wrong: " + str(e) 
            return render_template('home.html',
                                    err=e)
        # Compile return data in one thicc dict
        return_data = {"depart_station" : depart_station,
            "arrive_station" : arrival_station,
            "train_list" : trains, "time" : data["Input Time"],
            "depOrArr" : data["DepOrArr"]}

        return render_template('home.html', return_data=return_data)
    else:
        return render_template('home.html')


def normalise(str):
    temp_str = str[1:-1]
    result = []
    for item in temp_str.split(', '):
        result.append(item[1:-1])
    return [tuple(result)]
