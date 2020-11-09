import os

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

INTENT_VERIFY_IDENTITY = 'VerifyIdentity'
INTENT_NO = 'No'
INTENT_YES = 'Yes'
INTENT_NOT_SUPPORTED = 'NotSupported'

# medication bot
BOT_MEDICATION_NAME = 'Medication'
INTENT_MEDICATION_TIME = 'MedicationTime'
INTENT_YES_MEDICATION = 'YesMedication'
INTENT_NO_MEDICATION = 'NoMedication'

SLOT_MED_TIME = 'med_time'
SLOT_MED_TIME_OF_DAY = 'time_of_day'

# symptom bot
BOT_SYMPTOM_NAME = 'SymptomReport'
INTENT_REPORT_SYMPTOM = 'ReportSymptom'
INTENT_YES_SYMPTOM = 'YesSymptom'
INTENT_NO_SYMPTOM = 'NoSymptom'
INTENT_SYMPTOM_FALLBACK = 'SymptomFallback'
INTENT_PAIN_EXTENT = 'NoSymptom'
SLOT_SYMPTOM_ONE = 'symptom'
SLOT_BODY_PART = 'bodyPart'
SLOT_BODY_PART_MODIFIER = 'modifier'
SLOT_PAIN_LEVEL = 'painLevel'

# identity
SLOT_ZIPCODE = 'zipcode'
AUTH_RESULT_ATTR = 'AuthResult'

# quality of life
BOT_QUALITY_OF_LIFE_NAME = 'QualityOfLife'
INTENT_NUMERIC_RATING = 'NumericRating'
INTENT_DESCRIPTIVE_RATING = 'DescriptiveRating'
SLOT_NUMERIC_PROBLEM_LEVEL = 'problemLevel'
SLOT_QUALITATIVE_PROBLEM_LEVEL = 'qualitativeRating'
INTENT_REPEAT = 'Repeat'

# confirm report time
INTENT_YES_REPORT_NOW = 'YesReportNow'
INTENT_NO_LATER = 'NotAGoodTime'
