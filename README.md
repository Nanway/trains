# where-the-trains-at

- this is the real version

This is a Flask based web app where a user can choose train stations (in the Sydney Trains network) and retrieve a train timetable adjusted to their departure/ arrival times. What makes it non-trivial is that on my daily commute to university (from Strathfield to Central), I often realise that there are intercity express trains that are 'set-down' only at Strathfield and thus don't come up in tripview, the station scrolling screens or the TFNSW trip planner. The express trains generally come at convenient times between normal trains. However, I would have to walk up and down the express train platform to see if there is an express train coming soon. So I made this app to save me the effort in walking up and down a ramp.

This app has been deployed to: https://where-the-trains-at.herokuapp.com/ (as it is hosted for free, if unused for 30 minutes the server shuts down and thus needs time to load after a period of inactivity)

Updates:
- First release had a very slow app (~10 seconds to retrieve timetables). I profiled the code and realised it was because the API calls took around 1 second each and I make plenty of them. To solve this I found ways to minimise the number of API calls I made. I built a dictionary with common stop IDs so that I didn't need to call the stop finder API, redesigned the code so that it found express trains with less API calls and introduced asynchronous API calls. Time reduced from 10 seconds to 4.

How it works:
- Parse the input on the web page, use the Stop Finder API to find the ID of the stops inputted. Pass these IDs and other user provided info into Trip API and filter the results as necessary. https://opendata.transport.nsw.gov.au/node/601/exploreapi#!/default/tfnsw_trip_request2
- To find shortcuts I use  the trip planner APIs and for "Depart At" I search for trains from Epping/ Parramatta to Central that depart with a 30 min offset (see code comments for explanation of how I arrived at this value) and I check if Strathfield is enroute and pull out the departure time from strathfield. "Arrive By" is similar but I just check arrival times at Central.
- I then collect the top 5 results and pass it back into the web page
- Host locally with python run.py

Learnings:
- I learnt how to understand technical documentation from Transport For NSW in order to make the correct API calls and interpret the results correctly
- Learnt how to make API requests and interpret and parse the json return file in Python
- Was able to apply some design principles that I learnt in class (OCP in the API_requesters) for better design.
- Learnt how to include a bootstrap template in web pages and developed further understanding of html 
- Learnt that the server time on TFNSW is actually 'Zulu' (or UTC time)
- Learnt how to run async code (aiohttp + asyncio) in python + learnt how to profile code for optimization
- Learnt how to deploy an app somewhere onto the internet

Current limitations:
- Takes ~4 seconds to find a shortcut due to API request time. I've attempted to make asynchronous calls but still am trying to find ways to reduce the time.
- App is hosted on a free server in America somewhere that shuts down after 30 minutes of inactivity. This also contributes to the speed issues.
- Only works for direct trips
- Needs further testing. I have tested it with existing timetables and it finds all suitable trains but I have yet to think of any edge cases
- Only searches for today's trains

