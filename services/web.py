import logging
from urllib.parse import urljoin
import json

from requests import Session
from requests.exceptions import RequestException

WEATHER_KEY = '8fe40567ff300e84bde233ea59e73fc5'
with open('services/city.list.json') as file:
    CITIES = json.load(file)

CURRENCY_CODES = ['USD', 'GBP', 'CAD', 'EUR', 'RUB', 'JPY']

logger = logging.getLogger(__name__)


class API:
    def __init__(self, url='', api_key=''):
        self.session = Session()
        self.base_url = url
        self.api_key = api_key
        self.api_url = None

    def request(self, request_string):
        service_unavailable = 'Sorry, service is temporary unavailable'
        url = urljoin(self.base_url, request_string)
        try:
            response = self.session.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                return service_unavailable
        except RequestException as e:
            logger.warning(e)
            return service_unavailable

    def create_api_string(self, **kwargs):
        params_string = ''
        for key, value in kwargs.items():
            param = '{key}={value}&'.format(key=key, value=value)
            params_string += param

        formatted_params_string = params_string.rstrip('&')
        api_string = '{api_url}?{params_string}'.format(api_url=self.api_url, params_string=formatted_params_string)

        return api_string


class Weather(API):

    def __init__(self, city_name='', location=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_url = '/data/2.5/'
        self.city = {}
        if city_name:
            self.city['name'] = city_name
        if location:
            self.city['location'] = {'lon': location.longitude,
                                     'lat': location.latitude}

    def _get_data(self):
        city_id = self._get_city_id()
        if city_id:
            api_string = self.create_api_string(id=city_id, appid=self.api_key, units='metric')
            return self.request(request_string=api_string)

        return None

    def _get_city_id(self):
        city_id = None
        if CITIES:
            if self.city:
                for city in CITIES:
                    longitude = city['coord']['lon']
                    latitude = city['coord']['lat']
                    city_name = city['name']
                    if 'name' in self.city:
                        if city_name.lower() == self.city['name'].lower():
                            city_id = city['id']
                    elif 'location' in self.city:
                        if abs(longitude - self.city['location']['lon']) < 0.07 and \
                                abs(latitude - self.city['location']['lat']) < 0.07:
                            city_id = city['id']
        return city_id

    @staticmethod
    def _wind_degree_converter(degree):
        directions = ['North', 'North-northeast', 'Northeast', 'East-northeast',
                      'East', 'East-southeast', 'Southeast', 'South-southeast',
                      'South', 'South-southwest', 'Southwest', 'West-southwest',
                      'West', 'West-northwest', 'Northwest', 'North-northwest',
                      'North']
        sector = 360 / 16
        cardinal = int((degree + sector / 2) / 22.5)
        return directions[cardinal]

    def _formatted_data(self, data):
        wind_speed = data['wind']['speed']
        wind_degree = data['wind']['deg']
        wind = '{direction}, {speed} meter/sec'.format(direction=self._wind_degree_converter(wind_degree),
                                                       speed=wind_speed)
        pressure = data['main']['pressure']
        pressure_in_mmhg = int(pressure * 100 * 0.00750062)  # we convert pressure from Pa into mmHg.
        formatted_data = {'pressure': pressure_in_mmhg,
                          'temp': int(data['main']['temp']),
                          'humidity': data['main']['humidity'],
                          'wind': wind,
                          'name': data['name']
                          }

        return formatted_data

    def _current(self):
        self.api_url += 'weather'
        data = self._get_data()

        if isinstance(data, dict):
            return self._formatted_data(data)
        elif data:
            return data

        return None

    def current(self):
        return self._current()


class Currency(API):

    def __init__(self, currency='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_url = '/v4/latest/'
        self.currency = None
        if currency and currency.upper() in CURRENCY_CODES:
            self.currency = currency.upper()

    def _get_data(self):
        data = None
        if self.currency:
            url = '{api_url}{currency}'.format(api_url=self.api_url, currency=self.currency)
            data = self.request(request_string=url)
        return data

    def _formatted_data(self):
        data = self._get_data()

        if isinstance(data, dict):
            formatted_data = {}
            unformatted_data = data['rates']
            for currency, value in unformatted_data.items():
                key = '{base}/{currency}'.format(base=self.currency, currency=currency)
                if currency == self.currency:
                    continue
                if currency in CURRENCY_CODES:
                    formatted_data[key] = value
            return formatted_data

        return data

    def latest_rates(self):
        return self._formatted_data()
