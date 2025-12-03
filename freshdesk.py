import requests
import os
import datetime

from config import (
    FRESHDESK_GROUP,
    FRESHDESK_API_URL
)

auth = (os.environ['FRESHDESK_API_TOKEN'], 'X')


def get_tickets(page: int, start_range: datetime.datetime, end_range: datetime.datetime) -> list:
    headers = {
        "Content-Type": "application/json"
    }

    params = {
        "query": f"\"group_id:{FRESHDESK_GROUP} AND (created_at:>'{start_range.strftime('%Y-%m-%d')}' AND created_at:<'{end_range.strftime('%Y-%m-%d')}')\"",
        "page": page
    }

    print(params)

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