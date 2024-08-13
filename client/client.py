import hashlib
import hmac
import time
import json
import aiohttp
import ssl
import logging
from datetime import datetime



PAYLOAD_KEY_METHOD = 'method'
PAYLOAD_KEY_PATH = 'path'

REQUIRED_KEYS = [PAYLOAD_KEY_METHOD, PAYLOAD_KEY_PATH]

def hex2bytes(value: str) -> bytes:
    if value.startswith('0x'):
        value = value[2:]
    return bytes.fromhex(value)

class Payload:
    def __init__(self, timestamp: int, data: dict[str, str]):
        self.timestamp = timestamp
        self.data = data

        for k in REQUIRED_KEYS:
            if k in data:
                continue
            raise KeyError(f'Missing required key: {k}')

    @property
    def hash(self) -> bytes:
        '''
        Returns the hash of the payload where the params are sorted in
        alphabetical order.
        '''
        keys = list(self.data.keys())
        keys.sort()
        message = [f'{k}={str(self.data[k]).lower()}' if isinstance(self.data[k], bool) else f'{k}={self.data[k]}' for k in keys]
        message.append(str(self.timestamp))
        message = ''.join(message)

        h = hashlib.sha256()
        h.update(message.encode())

        return h.digest()

    def sign(self, secret: str) -> str:
        '''
        Returns HMAC-SHA256 signature after signing payload hash with
        user secret.
        '''
        secret_bytes = hex2bytes(secret)
        return '0x' + hmac.new(secret_bytes, self.hash, hashlib.sha256).hexdigest()

    def verify(self, signature: str, secret: str) -> bool:
        expected_signature = self.sign(secret)
        if expected_signature != signature:
            return False

        current_timestamp = int(datetime.now().timestamp())
        if current_timestamp >= self.timestamp:
            return False

        return True


class ExchangeClient:
    def __init__(self, api_key, secret_key, base_url, eid="BFX"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.eid = eid
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def _expiration_timestamp(self):
        return int(time.time()) + 60  # Expires in 60 seconds

    def generate_signature(self, data):
        """
        Generates a signature using the Payload class.
        """
        expiration_timestamp = self._expiration_timestamp()
        payload = Payload(expiration_timestamp, data)
        signature = payload.sign(self.secret_key)
        return signature, expiration_timestamp

    def headers(self, signature: str, expiration_timestamp: int) -> dict[str, str]:
        headers = {
            'RBT-TS': str(expiration_timestamp),
            'RBT-SIGNATURE': signature,
            'EID': self.eid
        }
        if self.api_key:
            headers['RBT-API-KEY'] = self.api_key
        return headers


    async def send_request(self, endpoint, params, method="POST"):
        """
        Sends a signed request to the exchange using aiohttp.
        """
        params[PAYLOAD_KEY_METHOD] = method.upper()
        params[PAYLOAD_KEY_PATH] = endpoint
    
        signature, expiration_timestamp = self.generate_signature(params)
    
        headers = self.headers(signature, expiration_timestamp)
    
        url = f'{self.base_url}{endpoint}'
        async with aiohttp.ClientSession() as session:
            try:
                if method == "POST":
                    async with session.post(url, headers=headers, json=params, ssl=self.ssl_context) as response:
                        response.raise_for_status()  
                        return await response.json()
                elif method == "GET":
                    async with session.get(url, headers=headers, params=params, ssl=self.ssl_context) as response:
                        response.raise_for_status()  
                        return await response.json()
                elif method == "PUT":
                    async with session.put(url, headers=headers, json=params, ssl=self.ssl_context) as response:
                        response.raise_for_status()  
                        return await response.json()
                elif method == "DELETE":
                    async with session.delete(url, headers=headers, params=params, ssl=self.ssl_context) as response:
                        response.raise_for_status()  
                        return await response.json()
                else:
                    raise ValueError("Invalid HTTP method specified. Use 'GET', 'POST', 'PUT', or 'DELETE'.")
    
            except aiohttp.ClientResponseError as err:
                logging.error(f"HTTP error occurred: {err.message}")
                raise
    
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                raise


class OrderClient(ExchangeClient):
    def __init__(self, api_key, secret_key, base_url, eid="BFX"):
        super().__init__(api_key, secret_key, base_url, eid)

    async def get_order_status(self, order_id=None, client_order_id=None, status=None, market_id=None,
                               start_time=None, end_time=None, p_limit=100, p_page=0, p_order="DESC"):
        """
        Get the status of account orders.
        """
        params = {
            "order_id": order_id,
            "client_order_id": client_order_id,
            "status": status,
            "market_id": market_id,
            "start_time": start_time,
            "end_time": end_time,
            "p_limit": p_limit,
            "p_page": p_page,
            "p_order": p_order
        }

        params = {k: v for k, v in params.items() if v is not None}

        logging.info(f"Requesting order status with params: {json.dumps(params, indent=2)}")

        return await self.send_request("/orders", params, method="GET")

    async def place_order(self, market_id, price, side, size, order_type="market",
                          time_in_force="good_till_cancel"):
        """
        Place a limit or market order.
        """
        params = {
            "market_id": market_id,
            "price": price,
            "side": side,
            "size": size,
            "type": order_type,
            "time_in_force": time_in_force
        }

        params = {k: v for k, v in params.items() if v is not None}

        logging.info(f"Placing order with params: {json.dumps(params, indent=2)}")

        return await self.send_request("/orders", params, method="POST")
