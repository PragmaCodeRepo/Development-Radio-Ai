from datetime import datetime, timedelta


def schedule_time_date_time_format_converter(schedule_time_str):
    try:
        # Try to parse the timestamp using the first format
        schedule_time = datetime.strptime(
            schedule_time_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        try:
            # If the first format fails, try the second format
            schedule_time = datetime.strptime(
                schedule_time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            print(
                f"Unable to parse schedule_time_str: {schedule_time_str}")
            raise
    return schedule_time
