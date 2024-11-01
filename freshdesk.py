import requests
import os

from config import (
    FRESHDESK_GROUP,
    FRESHDESK_API_URL
)

auth = (os.environ['FRESHDESK_API_TOKEN'], 'X')


def get_tickets(page: int = 1):
    headers = {
        "Content-Type": "application/json"
    }

    params = {
        "query": f'"group_id:{FRESHDESK_GROUP}"',
        "page": page
    }

    response = requests.get(f'{FRESHDESK_API_URL}search/tickets', params=params, auth=auth, headers=headers)

    return response.json()['results']


def get_contact(id:int):

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.get(f'{FRESHDESK_API_URL}contacts/{id}', auth=auth, headers=headers)

    if response.ok:
        return response.json()

    return {'name': None, "email": None}