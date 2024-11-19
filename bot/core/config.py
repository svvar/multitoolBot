import configparser

_config = configparser.ConfigParser()
_config.read('./config.ini')


TOKEN = _config['bot']['token']
ADMINS = [int(x) for x in _config['bot']['admins'].split(',')]

PROXY_PROTOCOL = _config['proxy']['protocol']
PROXY_HOST = _config['proxy']['host']
PROXY_PORT = _config['proxy']['port']
PROXY_USERNAME = _config['proxy']['username']
PROXY_PASSWORD = _config['proxy']['password']
PROXY_ROTATE = _config['proxy']['change_link']

AI_API_TOKEN = _config['gemini']['API_TOKEN']
