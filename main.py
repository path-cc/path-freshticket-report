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


def get_past_application_tickets(cutoff: datetime.datetime) -> list:

    tickets = []

    for x in range(1,10):  # Max out at 300 tickets
        ticket_page = get_tickets(page=x)

        for ticket in ticket_page:
            if datetime.datetime.strptime(ticket['created_at'], '%Y-%m-%dT%H:%M:%SZ') < cutoff:
                return tickets

            if ticket['subject'] == 'OSPool User - Account Creation':
                ticket['requester'] = get_contact(ticket['requester_id'])
                tickets.append(ticket)

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
        **parse_html_to_dict(t['description'])
    }


def parse_html_to_dict(html: str) -> dict:
    pattern = re.compile(r'<h3>(.*?)<\/h3>\s*<div>(.*?)<\/div>', re.DOTALL)
    matches = pattern.findall(html)
    return {match[0].strip(): match[1].strip() for match in matches}


def main() -> None:

    try:
        fresh_tickets_dirty = get_past_application_tickets(datetime.datetime.now() - datetime.timedelta(days=63))
        fresh_tickets = list(map(clean_ticket, fresh_tickets_dirty))

        report = pd.DataFrame(fresh_tickets)

        # Reporting period:
        # Starts:         At the most recent strat of month
        # Ends:           At the most recent end of month
        today = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0))
        report_end = (today.replace(day=1) - datetime.timedelta(days=1)).replace(hour=23, minute=59, second=59)
        report_start = report_end.replace(day=1, hour=0, minute=0, second=0)

        # Filter out the tickets that were created after the start of the reporting period
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
                f"Attached is a monthly report on freshdesk applications.\nThis report is generated via code saved here: https://github.com/path-cc/path-freshticket-report\n\n",
                [report_path],
                SMTP_SERVER
            )

    except Exception as e:

        send_email(
            'clock@wisc.edu',
            ['clock@wisc.edu', 'chtc-freshdesk-report@g-groups.wisc.edu'],
            "Monthly Freshdesk Report Failure",
            f"Monthly report on freshdesk applications failed!!!\n\n Errors Recorded: {e}",
            [],
            SMTP_SERVER
        )


if __name__ == "__main__":
    main()
