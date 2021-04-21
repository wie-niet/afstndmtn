import requests
import os
from lxml import etree

from tabulate import tabulate

import simplejson as json

"""
afstndmtn :
# usage:
import afstndmtn

# init api
api = afstndmtn.Api()

# search 
s = api.search(text='runforestrun')   # search for any text with 'runforestrun'
afstndmtn.Display( s )                # table view of search results


# first route from search results
r = s.result[0]                       
afstndmtn.Display( r )                # table view of route

# login
api.login('user', 'secret')
afstndmtn.Display( api.session )      # table view of session

# add to favorites:
api.tools.add_favorite(r)
afstndmtn.Display( api.favorite.refresh() )

# lookup favorites
api.favorite.search()                 # fetch favorites
afstndmtn.Display( api.favorite )     # table view of search results

# delete from favorites:
api.tools.delete_favorite(r)
afstndmtn.Display( api.favorite.refresh() )


# lookup private
api.private.search()                  # fetch private
afstndmtn.Display( api.private )      # table view of search results


# login
# api.logout()

#
# easy display command, handy for command line use or debugging:
# display Search/Route/Session object: afstndmtn.Display( obj )
#
afstndmtn.Display( s )               # table view of search results
afstndmtn.Display( r )               # table view of route
afstndmtn.Display( api.session )     # table view of session

"""
	

class Route:
	def __init__(self, init_dict={}):
		for (key, value) in init_dict.items():
			setattr(self, key, value)


	def __repr__(self):
		return '<{}.{}(id:{})>'.format(self.__class__.__module__, self.__class__.__name__, self.id)

	@property
	def url_gpx(self):
		return 'https://www.af'+'stan'+'dmeten.nl/processExportFile.php?route_id={}&export=Exporteer+naar+GPX'.format(self.id)

			
	def _asdict(self):
		"""simplejson helper"""
		return self.__dict__





class Tools:
	def __init__(self, api):
		"""this class is initialised as tools attrib on an Api() instance"""
		# set api
		self.api = api
		
	def __return_ids_from_routes(self, routes):
		"""return all ids in an list """
		ids=[]
		
		# single route
		if isinstance(routes, Route):
			ids.append(routes.id)
			return(ids)

		# list of routes
		for route in routes:
			ids.append(route.id)
			
		return ids	
	
	def add_favorite(self, routes):
		"""add routes (route , or [route, ...]) to favorite"""
		
		ids = self.__return_ids_from_routes(routes)
		
		if len(ids) == 0:
			raise AttributeError('you must specify atleast one route')
			
		if self.api.session.authenticated is False:
			raise RuntimeError("You must authenticate to add_favorite")	
			
		# make comma seperated list of ids	
		data = {'ids': ','.join(ids) }
		
		# post
		res = self.api.requests.post('https://www.af'+'standm'+'eten.nl/addFavorite.php', data)

		# debug:
		print(res.text)


	def delete_favorite(self, routes):
		"""delete routes (route , or [route, ...]) from favorite"""
		
		ids = self.__return_ids_from_routes(routes)
		
		if len(ids) == 0:
			raise AttributeError('you must specify atleast one route')
			
		if self.api.session.authenticated is False:
			raise RuntimeError("You must authenticate to delete_favorite")	
			
		# make comma seperated list of ids	
		data = {'route_ids': ','.join(ids)  }
		data['login'] = self.api.session.user_id
		
		# post
		res = self.api.requests.post('https://www.a'+'fstandm'+'eten.nl/deleteFavorite.php', data)
		self._http = res
		# debug:
		print(res.text)

	def delete_route(self, routes):
		"""delete route (route , or [route, ...])"""
		
		ids = self.__return_ids_from_routes(routes)
		
		if len(ids) == 0:
			raise AttributeError('you must specify atleast one route')
			
		if self.api.session.authenticated is False:
			raise RuntimeError("You must authenticate to delete_favorite")	
			
		# make comma seperated list of ids	
		data = {'route_ids': ','.join(ids)  }
		
		# post
		res = self.api.requests.post('https://www.af'+'sta'+'ndmeten.nl/deleteRoute.php', data)
		self._http = res
		# debug:
		print(res.text)

	def filename_gpx(self, route, prefix_dir=None):
		gpx_filename = '{}.gpx'.format(route.title)
		
		if prefix_dir:
			gpx_filename = '{}{}{}'.format(prefix_dir, os.path.sep, gpx_filename)
		
		return(gpx_filename)
		
	def download_gpx(self, route, download_dir="./"):
		"""download gpx file (route)"""
		
		gpx_filename = self.filename_gpx(route, download_dir)
		
		if os.path.exists(gpx_filename):
			raise FileExistsError('file {} does already exist!'.format(gpx_filename))
			
		r = requests.get(route.url_gpx)
		
		with open(gpx_filename, 'w') as f:
			f.write(r.text)
			
			

class Search():
	# raw POST options
	#  cat: 'browse' # static === table browse ?? 
	#  methods: {location: "Publiek", myroutes: "Prive", favoriet: "Favoriet"} # default = methods:'location'
	#  m: activity, default = "alle" (~ means "All/Any" in dutch)
	#  l: Country (~dutch land), default "alle" (~ means "All/Any" in dutch)
	#  pr: provincie, default: 'alle' (no other options in form.., only after selecting 'l'(country) )
	#  t: free text search. example= "Fietsen"
	#  s: ['titel', 'Gebruikers.naam'] free text search attribute, 
	#	 ['titel', 'Gebruikers.naam'] match 'titel' (~title) | 'Gebruikers.naam' (~Username)
	#  a_min: '' # minimum distance in km, use empty string ('') to disable
	#  a_max: '' # maximum distance in km, use empty string ('') to disable
	
	
	# translate search text_option
	__TEXT_OPTION = {'title': 'titel', 'username': 'Gebruikers.naam'}
	
	
	
	def __init__(self, text=None, text_option=None, folder=None, search=True, api=None):
		"""call this via search() method on an Api() instance"""
		# set api or initialize a new one:
		self.api = api if api is not None else Api()
		
		# results:
		self.__result = None
		
		# default options:
		self.__options = {'cat':'browse', 'methods':'location', 'm':'alle', 'l':'alle', 't':'', 's':'titel', 'a_min':'', 'a_max':'', 'nr_page':500, 'sorton':'bDESC'}

		go_search = False
		
		# search text
		if text is not None:
			self.text = text
			go_search = True
			
		if text_option is not None:
			self.text_option = text_option
				
		# folder
		if folder is not None:
			self.folder = folder
			
		# search 
		if search and go_search:
			self.search()
	
	
	@property
	def has_result(self):
		return isinstance(self.__result, list)
	
	@property
	def result(self):
		if self.__result is None:
			# only when Search.__options has changed
			if self.text == '' and self.folder == 'public':
				# TODO: limit only to text, place / location etc.. 
				raise AttributeError('set any search argument before searching')
			
			self.search()
		
		return self.__result
			
			
	# text
	@property
	def text(self):
		return self.__options['t']
		
	@text.setter
	def text(self, search_text):
		# clear all results
		self.__result = None

		self.__options['t'] = search_text

	
	# text_option
	@property
	def text_option(self):
		# lookup key by value in __TEXT_OPTION
		return list(self.__TEXT_OPTION.keys())[list(self.__TEXT_OPTION.values()).index( self.__options['s'] )]
		
	@text_option.setter
	def text_option(self, text_option):
		"""["title" or "username"]"""

		# clear all results
		self.__result = None
		
		if text_option not in self.__TEXT_OPTION:
			raise AttributeError('text_option does not match "title" or "username"')
			
		# translate into dutch API name 	
		self.__options['s'] = self.__TEXT_OPTION[ text_option ]

	# max_results
	@property
	def max_results(self):
		return self.__options['nr_page']

	@max_results.setter
	def max_results(self, max_results):	
		# clear all results
		self.__result = None

		self.__options['nr_page'] = str(max_results)
		

	# min_km
	@property
	def min_km(self):
		return self.__options['a_min']

	@min_km.setter
	def min_km(self, value):	
		# clear all results
		self.__result = None
		self.__options['a_min'] = str(value)

	# max_km
	@property
	def max_km(self):
		return self.__options['a_max']

	@max_km.setter
	def max_km(self, value):	
		# clear all results
		self.__result = None
		self.__options['a_max'] = str(value)


	# activity
	@property
	def activity(self):
		return self.__options['m']

	@activity.setter
	def activity(self, value):	
		# clear all results
		self.__result = None
		self.__options['m'] = str(value)



	# result_order
	@property
	def results_order(self):
		return self.__options['sorton']

	@results_order.setter
	def results_order(self, order):	
		# clear all results
		self.__result = None

		if order not in ['bDESC', 'bASC', 'aDESC', 'aASC', 'tDESC', 'tASC']:
			raise AttributeError('results_order {} not allowed'.format(order))
			
		self.__options['sorton'] = order

	# folder:
	__METHODS={'public': "location", 'private': "myroutes", 'favorite': "favoriet"}
	@property
	def folder(self):
		return list(self.__METHODS.keys())[list(self.__METHODS.values()).index( self.__options['methods'] )]
		
	@folder.setter
	def folder(self, name):
		# clear all results
		self.__result = None

		if name not in self.__METHODS:
			raise AttributeError("folder doesn't match ['public', 'private', 'favorite']")	
		
		self.__options['methods'] = self.__METHODS.get(name)
		
			
	def refresh(self):
		return self.search()

	def search(self):
		# folder ['private', 'favorite'] works only when authenticated
		if self.folder in ['private', 'favorite'] and self.api.session.authenticated is False:
			raise RuntimeError("You must authenticate for accessing the '{}' folder".format(self.folder))
		
		# HTTP request:
		res = self.api.requests.post('https://www.afs'+'tan'+'dmeten.nl/browse.php', self.__options)
		
		# # keep http response, handy for debug use:
		# self._http = res
		
		# parse html and get routes
		self.__result = self.__parse_search_result(res.text)
		
		# return self
		return(self)
		
	def __parse_search_result(self, rawhtml):
		results = []
		
		# itterate over second table from html
		for row in etree.HTML(rawhtml).find("body/div/form/table[2]"):
			result = {} # dict for all results
			
			try:
				# route id (<td [0]><input value="..." ) 
				result['id'] = row[0].getchildren()[0].attrib['value']
				
			except IndexError as e:
				# will fail with IndexError for row[0] and row[n-1]
				# skip first row and last row
				pass
		
			# we found an id, get more results:
			if 'id' in result:
				# route date (<td [3]> ... )
				result['date'] =  row[3].text
				
				# route title (<td [4]> <a> __ ... )
				result['title'] = row[4].getchildren()[0].text.lstrip()

				# route username (<td [5]> __ ... __ )
				result['username'] = row[5].text.strip()
				
				# route distance (td [6]> ... __)
				result['distance'] = row[6].text.strip()
				
				# route view_count (<td [7]> .... )
				result['view_count'] = row[7].text.strip()
				
				# route location_name (<td [8]> ... __ )
				result['location_name'] = row[8].text.strip()
				
				# route activity_type (<td [1]> <img title="...")
				result['activity_type_nl'] = row[1].getchildren()[0].attrib['title']
				
				
				results.append(Route(result))

		return results
		

	#
	# def __iter__(self):
	# 	"""simplejson helper"""
	# 	return self.result.__iter__()
	#
	# def __getitem__(self, idx):
	# 	return self.result[idx]
	#
	# def __len__(self):
	# 	return len(self.result)
		
		
class Session:
	username = None
	user_id = None
	user_city = None
	user_country = None
	authenticated = False
	
	def __init__(self, api):
		"""this class is initialised as session attrib on the Api()"""
				
		# api
		self.api = api 
		
		# http requests 
		self.requests = requests.Session()
		
	

	def login(self, username, password):
		data = {'login':username, 'password':password}
		
		res = self.requests.post('https://www.af'+'stand'+'met'+'en.nl/login.php', data)

		# #DEBUG
		# self._http_login = res
		
		# html etree
		html = etree.HTML(res.text)
				
		# authentication succesfull
		if res.text.find('<span style="color:red">') > 1:
			# Username or Password was wrong:
			self.__cleanup()
			raise RuntimeError('Login unsucsesfull: {}'.format(html.xpath('//span[@style="color:red"]')[0].text))
		
		
		# we are logged on.
		self.authenticated = True
		
		# login_id
		self.user_id = html.xpath("//input[@name='login']/@value")[0]

		# username:
		self.username = html.xpath('//legend[ contains(., "Acties voor ")]')[0].text.replace('Acties voor ','',1)
		
		# city
		self.user_city = html.xpath("//input[@name='gotoWoonplaats']/@value")[0]
		
		# country
		self.user_country = html.xpath("//input[@name='gotoLand']/@value")[0]
		
	
	def __cleanup(self):
		self.authenticated = False
		self.username = None
		self.user_id = None
		self.user_city = None
		self.user_country = None
		
	def logout(self):
		res = self.requests.post('https://www.afs'+'tand'+'meten.nl/logout.php', {})
		self.__cleanup()



class Api:
	session = None
	requests = None
	
	def __init__(self):
		# set session object
		self.session = Session(api=self)
		
		# shortcut to requests:
		self.requests = self.session.requests
		
		# tools
		self.tools = Tools(api=self)
		
		# my folders:
		self.private = self.search(folder='private')
		self.favorite = self.search(folder='favorite')
		
		
	def search(self, *args, **kwargs):
		return Search(api=self, *args, **kwargs)
	
	def login(self, username, password):
		self.session.login(username, password)

	def logout(self):
		self.session.logout()
		


class Display:
	
	def __new__(cls, obj, display_type='table',  *args, **kwargs):
		"""Display Objects in fashionable way. display them in table etc.."""
		cls.display(obj,display_type, *args, **kwargs)
	
	@classmethod
	def display(cls, obj, display_type='table', *args, **kwargs):
		"""Display Objects in fashionable way. display them in table etc.."""
		getattr(cls, 'display_{}_{}'.format(obj.__class__.__name__.lower(),display_type))(obj, *args, **kwargs)
	
	#
	# Session
	#
	
	@classmethod
	def display_session_table(cls, obj):
		"""display session info in tabular fashion"""
		data = []
		for key in ['authenticated', 'username', 'user_id', 'user_city', 'user_country']:
			data.append({ 'key': key,  'value': str(getattr(obj, key)) })			
		print(tabulate( data ))


	#
	# Search 
	#
	SEARCH_TABLE_MIN={'id':'id#', 'date':'Date', 'title':'Title', 'distance':'km', 'username':'Author'}
	SEARCH_TABLE_ALL={'id':'id#', 'date':'Date', 'title':'Title', 'distance':'km', 'username':'Author', 'view_count':'#', 'activity_type_nl':'Activity','location_name':'Location'}
	SEARCH_TABLE_DEFAULT=SEARCH_TABLE_ALL

	SEARCH_OPTIONS={'folder':'folder', 'activity':'activity', 'text':'text', 'text_option':'text_option', 'min_km':'min_km', 'max_km':'max_km'}
		
	@classmethod
	def display_search_table(cls, obj, cols=SEARCH_TABLE_DEFAULT, search_options=True, options_cols=SEARCH_OPTIONS):
		""""""
		
		if search_options:
			options_s = " "
			for k in options_cols.keys():
				options_s += " {}='{}';".format(k, getattr(obj, k, None))
				
			#print(tabulate([ options ], headers=options_cols))
			print("[ Search options:{}]".format( options_s )) 
			
		
		data = []
		if not obj.has_result:
			print ("## serach hasn't been queried out.")
		else:	
			for route in obj.result:
				item = {}
				for col in cols.keys():
					item[ col ] = getattr(route, col, None)
			
				data.append(item)
		
			print(tabulate(data, headers=cols))
		print("Total: {}    (max results: {}; sort order: {})".format(len(data), obj.max_results, obj.results_order))	
		
	
	#
	# Route
	#	
	@classmethod
	def display_route_table(cls, obj):
		"""display info in tabular fashion"""
		data = []
		for key in obj.__dict__.keys():
			data.append({ 'key': key,  'value': str(getattr(obj, key)) })
			
		print(tabulate( data ))