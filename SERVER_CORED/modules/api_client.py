import requests
from modules.logger import Logger
import random

log = Logger()

class APIClient:
    def __init__(
        self,
        base_url: str,
        token: str = None,
        retries: int = 3,
        timeout: int = 10,
        proxies_list: list = None,
        verify_ssl: bool = True,
        cert: str = None
    ):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.retries = retries
        self.timeout = timeout
        self.proxies_list = proxies_list or []
        self.verify_ssl = verify_ssl
        self.cert = cert

    def _headers(self):
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f"Bearer {self.token}"
        return headers

    def _get_random_proxy(self):
        if not self.proxies_list:
            return None
        proxy = random.choice(self.proxies_list)
        log.info(f"Используется прокси: {proxy}")
        return {"http": proxy, "https": proxy}

    def _request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        for attempt in range(1, self.retries + 1):
            try:
                proxies = self._get_random_proxy()
                log.info(f"HTTP {method.upper()} Request to {url}. Attempt {attempt}.")
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    timeout=self.timeout,
                    proxies=proxies,
                    verify=self.verify_ssl,
                    cert=self.cert,
                    **kwargs
                )
                if response.ok:
                    log.info(f"Response {response.status_code}: {response.text}")
                    return response.json() if 'application/json' in response.headers.get('Content-Type', '') else response.text
                else:
                    log.warning(f"Failed Response {response.status_code}: {response.text}")
            except requests.RequestException as e:
                log.error(f"Request Error: {e} — Пробуем другой прокси...")
        log.warning("Все попытки исчерпаны. Запрос не выполнен.")
        return None

    def get(self, endpoint: str, params: dict = None):
        return self._request("get", endpoint, params=params)

    def post(self, endpoint: str, data: dict = None):
        return self._request("post", endpoint, json=data)

    def put(self, endpoint: str, data: dict = None):
        return self._request("put", endpoint, json=data)

    def delete(self, endpoint: str):
        return self._request("delete", endpoint)
