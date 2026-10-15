import calendar
import datetime
from datetime import date, time, timedelta

import pytz


def get_first_and_last_date_of_month(year: int, month: int) -> tuple:
    '''Returns the first and last date of a given month and year.'''

    first, last = calendar.monthrange(year, month)
    return datetime.date(year, month, 1), datetime.date(year, month, last)


def get_date_range(start_date: date, end_date: date) -> list[date]:
    '''Generates a list of dates between start_date and end_date inclusive.'''
    return [
        start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)
    ]


def format_to_date(date_string: str) -> date:
    ''' Formats a string to a date object. Expects format 'YYYY-MM-DD'. '''
    return datetime.datetime.strptime(date_string, "%Y-%m-%d").date()


def format_to_time(time_string: str) -> time:
    ''' Formats a string to a time object. Expects format 'HH:MM'. '''
    return datetime.datetime.strptime(time_string, "%H:%M").time()


def make_timezone_aware(date_time: datetime, tz: str = "UTC") -> datetime:
    '''Makes a naive datetime object timezone aware.'''
    try:
        tz_obj = pytz.timezone(tz)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f"Invalid timezone: {tz}")

    if date_time.tzinfo is None:
        date_time_obj = tz_obj.localize(date_time)
    else:
        date_time_obj = date_time.astimezone(tz_obj)

    return date_time_obj


def timezone_conversion(
    date_time: datetime, from_tz: str = "UTC", to_tz: str = "UTC"
) -> datetime:
    
    '''Converts a datetime object from one timezone to another.'''
    
    try:
        local_tz = pytz.timezone(from_tz)
        to_convert_tz = pytz.timezone(to_tz)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f"Invalid timezone: {from_tz}")
    local_datetime = (
        local_tz.localize(date_time)
        if date_time.tzinfo is None or date_time.tzinfo.utcoffset(date_time) is None
        else date_time
    )

    to_tz_datetime = local_datetime.astimezone(to_convert_tz)

    return to_tz_datetime