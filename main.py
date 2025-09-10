#!/usr/bin/env python3

import datetime
import os
import tempfile
from statistics import mean
import re

import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from send_email import send_email
from freshdesk import get_tickets, get_contact
from config import (
    SMTP_SERVER
)


def get_past_application_tickets(start_range: datetime.datetime, end_range: datetime.datetime) -> list:

    tickets = []

    page = 1
    last_ticket_date = start_range
    while True:
        # Freshdesk API has a hard limit of 10 pages of results, so if we hit page 11, we need to update the start_range to the last ticket date
        if page == 11:
            print("Hit page 11, updating the start range to the last ticket date")
            page = 1
            end_range = last_ticket_date
            continue

        ticket_page = get_tickets(page=page, start_range=start_range, end_range=end_range)

        # If no tickets are returned, break the loop
        if len(ticket_page) == 0:
            break

        for ticket in ticket_page:

            last_ticket_date = datetime.datetime.strptime(ticket['created_at'], '%Y-%m-%dT%H:%M:%SZ')

            if ticket['subject'] == 'OSPool User - Account Creation':
                ticket['requester'] = get_contact(ticket['requester_id'])
                tickets.append(ticket)

        page += 1

    # Run through tickets and remove duplicates ( same id )
    unique_tickets = {}
    for ticket in tickets:
        unique_tickets[ticket['requester']['email']] = ticket

    tickets = list(unique_tickets.values())

    return tickets


def get_ft_institution(description: str):
    pattern = re.compile(r'<h3>\nInstitution.?\n<\/h3>\n<div>\s(.*?)\s<\/div>', flags=re.M)
    search = re.search(pattern, description)
    return search.group(1)


def clean_ticket(t):
    return {
        "ft_name": t['requester']['name'],
        "ft_email": t['requester']['email'],
        "ft_created": datetime.datetime.strptime(t['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
        "ft_tags": ";".join(t['tags']),
        **parse_html_to_dict(t['description'])
    }


def parse_html_to_dict(html: str) -> dict:
    pattern = re.compile(r'<h3>(.*?)<\/h3>\s*<div>(.*?)<\/div>', re.DOTALL)
    matches = pattern.findall(html)
    return {match[0].strip(): match[1].strip() for match in matches}


def main(month: int= None, year: int = None) -> None:

    try:
        # Reporting period:
        # Starts:         At the most recent strat of month
        # Ends:           At the most recent end of month
        now = datetime.datetime.now()
        date = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0)  # default to previous month
        if month is not None and year is not None:
            date = date.replace(month=month, year=year)
        report_end = (date.replace(day=1, month=(date.month + 1)) - datetime.timedelta(days=1)).replace(hour=23, minute=59, second=59)
        report_start = report_end.replace(day=1, hour=0, minute=0, second=0)

        fresh_tickets_dirty = get_past_application_tickets(report_start, report_end)
        fresh_tickets = list(map(clean_ticket, fresh_tickets_dirty))
        report = pd.DataFrame(fresh_tickets)

        # Filter out the tickets that were not created in the reporting period
        report = report[report['ft_created'] >= report_start]
        report = report[report['ft_created'] <= report_end]

        title = f"Fresh Ticket Monthly Report ({report_start.strftime('%Y-%m-%d')} - {report_end.strftime('%Y-%m-%d')})"
        with tempfile.TemporaryDirectory() as tmp:

            report_period = f"{report_start.strftime('%Y-%m-%d')}-{report_end.strftime('%Y-%m-%d')}"

            report_path = os.path.join(tmp, f"osg-account-report-{report_period}.csv")
            report.to_csv(report_path, index=False)

            send_email(
                'clock@wisc.edu',
                ['clock@wisc.edu', 'chtc-freshdesk-report@g-groups.wisc.edu'],
                title,
                f"Attached is a monthly report on freshdesk applications.\nThis report is generated via code saved here: https://github.com/path-cc/path-freshticket-report\nView all reports here: https://groups.google.com/a/g-groups.wisc.edu/g/chtc-freshdesk-report\n\n",
                [report_path],
                SMTP_SERVER
            )

    except Exception as e:

        print(f"Error generating report: {e}")

        send_email(
            'clock@wisc.edu',
            ['clock@wisc.edu', 'chtc-freshdesk-report@g-groups.wisc.edu'],
            "Monthly Freshdesk Report Failure",
            f"Monthly report on freshdesk applications failed!!!\n\n Errors Recorded: {e}",
            [],
            SMTP_SERVER
        )


if __name__ == "__main__":
    main(month=8, year=2024)
