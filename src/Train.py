# Return 'train' to go from destination A and B
class Train():
	'''Properties:
		departure_details: Tuple (Station ID, Platform)
		arrival_details: Tuple (Station ID, Platform)
		times: Dict ('Departure':DateTime, 'Arrival':DateTime)
		DateTime in Sydney timezone ^
		Train_id: Integer representing train code
		line: String representing train line
	'''
	def __init__(self, depart, arrive, times, train_ID = 0, line = ''):
		# Departure and arrival are tuples (ID, Platform)
		self._departure_details = depart
		self._arrival_details = arrive
		# Dict (Departure: DateTime, Arrival: DateTime)
		self._times = times
		self._train_ID = train_ID
		self._line = line

	@property
	def line(self):
		return self._line

	@property
	def train_ID(self):
		return self._train_ID

	@property
	def departure_details(self):
		return self._departure_details
	
	@property
	def arrival_details(self):
		return self._arrival_details
	
	@property
	def times(self):
		return self._times

	# For equality check trip code (assuming tfnsw uses unique ones)
	def __eq__(self, obj):
		if isinstance(obj, Train) and (self.train_ID == obj.train_ID):
			return True
		else:
			return False

class Train_request(Train):
	'''Same as Train but slightly different (data format/ types differ)
	Properties:
		departure_details: Station ID
		arrival_details: Station ID
		times : only Departure or Arrival field is needed (in utc time)
		depOrArrive : String (values: 'dep',  'arrive')
	'''
	def __init__(self, depart, arrive, times, depOrArrive):
		super().__init__(depart, arrive, times)
		self._depOrArrive = depOrArrive

	@property
	def depOrArrive(self):
		return self._depOrArrive
	
	def change_departure(self, new):
		self._departure_details = new