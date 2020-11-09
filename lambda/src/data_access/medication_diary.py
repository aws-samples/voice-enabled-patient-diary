
from data_access.data_config import MED_DIARY_TABLE, format_date_time_to_str
from data_access.ddb_util import put_item_ddb


def log_med(patient_id, time_reported, med_taken, time_taken=None):
    item = {
        'Patient_ID': patient_id,
        'Time_Reported': format_date_time_to_str(time_reported),
        'Med_Taken': med_taken,
    }

    if time_taken:
        item['Time_Taken'] = format_date_time_to_str(time_taken)

    put_item_ddb(MED_DIARY_TABLE, item)
