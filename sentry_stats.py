"""
sentry stats functions
"""
from datetime import datetime, timedelta
from dateutil import parser
import requests
import pytz


class SentryStats(object):
    """
    class for getting sentry stats
    """
    def __init__(self, api_key, organization):
        """
        init
        """
        self.api_key = api_key
        self.organization = organization

    def _headers(self):
        return {"Authorization": "Bearer " + self.api_key}

    def retrieve_events(self, project, days):
        """
        retrieve a list of events for project that are within x days of today
        """
        result = []
        events, next_header = self.retrieve_events_raw(project)

        start_date = pytz.utc.localize(datetime.now()) - timedelta(days=days)

        while events:
            # go through the events and add them one by one if they are in
            # the date range
            for event in events:
                date_created = parser.parse(event["dateCreated"])
                if date_created > start_date:
                    result.append(event)
                else:
                    return result

            # if we got through the events and all of them were less than
            # the start date then we need to fetch more
            next_link = self.parse_next_url(next_header)
            if not next_link:
                return result

            events, next_header = self.retrieve_from_link(next_link)

        return result

    def retrieve_events_raw(self, project):
        """
        get the raw events for a particular project
        """
        link = "https://app.getsentry.com/api/0/projects/{}/{}/events/".format(
            self.organization, project)
        return self.retrieve_from_link(link)

    def retrieve_from_link(self, link):
        """
        a general utility function that grabs a payload from a link
        """
        result = requests.get(link, headers=self._headers())
        result.raise_for_status()
        payload = result.json()
        return payload, result.headers["Link"]

    def retrieve_projects_raw(self):
        """
        get a raw list of projects
        """
        link = "https://app.getsentry.com/api/0/projects/"
        return self.retrieve_from_link(link)

    @staticmethod
    def parse_next_url(link_header):
        """
        function that extracts the next URL
        from the headers returned by Sentry
        """
        # we might get one or more link parts separated by ','
        parts = link_header.split(",")
        for part in parts:
            # the element is assumed to have a link like this
            # <....>, if we don't have it - skip
            if part.find("rel=\"next\"") != -1:
                link = part[part.find("<")+1: part.find(">")]
                return link
        return None
