import requests
from abc import ABC, abstractmethod
from datetime import *
from aiohttp import ClientSession
import asyncio
import urllib
import os


class API_requester(ABC):
	# API Access globals
	api_key = os.environ.get('API_KEY')
	header = {'Authorization' : api_key}
	url_end_point =  'https://api.transport.nsw.gov.au/v1/tp/'

	''' Input: Train_req object (for trip_requester) or parameter string
		for stopfinder_requester
		Output: request response data
		Makes an API request given some parameters
	'''
	def make_request(self, params):
		print(self.header)
		r = requests.get(self._make_url(), headers=self.header,
			params=self._make_payload(params))
		r.raise_for_status()
		return r

	''' Input: Same as above but a list of objects
		Output: raw response data in list ordered the same way
		that the parameter list was ordered
		Does API requesting asynchronously
	'''
	def make_request1(self, param_list):
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		#loop = asyncio.get_event_loop()
		return loop.run_until_complete(asyncio.ensure_future(
			self._make_requests_async(param_list)))

	''' Input: list of train_request objects or list of stopfinder 
		parameter strings
		Output: request response data
		Makes an API request given some parameters
	'''
	async def _make_requests_async(self, param_list):
		tasks = []
		async with ClientSession() as session:
			for req_param in param_list:
				task = asyncio.ensure_future(self._fetch(req_param, 
						session))
				tasks.append(task)

			responses = await asyncio.gather(*tasks)
			return responses


	''' Input: train_req object, requesting session
		Return: response as json
		Fetches data asynchronously
	'''
	async def _fetch(self, params, session):
		async with session.get(self._make_url(), 
			headers= self.header,
			params=self._make_payload(params)) as resp:
				return await resp.json()

	''' Input: None
		Output: String for url endpoint to hit
	'''
	@abstractmethod
	def _make_url(self):
		pass

	''' Input: See above for definition of params
		Output: String for url endpoint to hit
	'''
	@abstractmethod
	def _make_payload(self, params):
		pass

# Finds all stops associated with a specific name
class StopFinder_requester(API_requester):
	def _make_url(self):
		return self.url_end_point + 'stop_finder'

	def _make_payload(self, params):
		payload = {
			'outputFormat' : 'rapidJSON',
			'type_sf' : 'any',
			'name_sf' : params,
			'coordOutputFormat' : 'EPSG:4326',
		}
		return payload


class Trip_requester(API_requester):
	def _make_url(self):
		return self.url_end_point + 'trip'

	def _make_payload(self, train_request):
		if train_request.times.get("Arrival"):
			time = train_request.times["Arrival"]
		else:
			time = train_request.times["Departure"]

		time = time.strftime("%H%M")

		payload = {
			'outputFormat' : 'rapidJSON',
			'coordOutputFormat' : 'EPSG:4326',
			'depArrMacro' : str(train_request.depOrArrive),
			'itdTime' : time,
			'type_origin' : 'any',
			'name_origin' : train_request.departure_details,
			'type_destination' : 'any',
			'name_destination' : train_request.arrival_details,
			'calcNumberOfTrips' : '10',
			'excludedmeans' : 'checkbox',
			'exclMOT_4' : '1',
			'exclMOT_5' : '1', 
			'exclMOT_7' : '1',
			'exclMOT_9' : '1',
			'exclMOT_11' : '1',
			'TfNSWTR' : 'true',
			'version' : '10.2.1.42'
		}
		return payload
