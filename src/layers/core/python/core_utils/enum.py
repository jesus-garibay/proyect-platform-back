from enum import Enum

__all__ = [
    "StatusLoanEnum",
    "PlatformCodeEnum",
    "ProcessCodeEnum",
    "ProcessInternalEnum",
    "PlatformOriginEnum",
    "ApplicationEnum"
]


class StatusLoanEnum(Enum):
    ACTIVE = 1
    IN_PROCESS = 2
    CLOSED = 3
    LATE = 4
    EXPIRED = 5
    REJECTED = 6


class PlatformOriginEnum(Enum):
    WALLET = 1
    JUVO = 2


class ApplicationEnum(Enum):
    LENDING = 'L'


class PlatformCodeEnum(str):
    DB_DYNAMO = "01"
    INSWITCH = "02"
    MAMBU_AWS = "03"
    MAMBU_NET = "04"
    JUVO = "05"
    MTS_CONNECTOR = "06"
    FILE_SYSTEM_S3 = "07"
    AUTHENTICATION = "08"
    BRAZE = "09"
    MOMO = "10"
    LAYER = "11"
    LAMBDA = "00"


class ProcessCodeEnum(str):
    ONBOARDING = "101"
    DASHBOARD = "102"
    MANUAL_PAYMENT = "003"
    DISBURSEMENT = "004"
    LOAD_OFFERS = "005"
    AUTOMATIC_DEBIT = "006"
    OTP_PROCESS = "007"
    TOKEN = "008"
    OFFER_VALIDITY_CHRON = "009"


class ProcessInternalEnum(str):
    AUTOMATIC_DEBIT = "AUTOMATIC_DEBIT"
    LAYER = "LAYER"
    UPDATE_LENDING_LOAN_OFFERS = "UPDATE_LENDING_LOAN_OFFERS"
    DASHBOARD_NOTIFICATIONS = "DASHBOARD_NOTIFICATIONS"
    INVOICE_NOTIFICATIONS = "INVOICE_NOTIFICATIONS"
    SMS_MISSING_LAST = "SMS_MISSING_LAST"
    SMS_PROGRESS_FLOW = "SMS_PROGRESS_FLOW"
    MAMBU_RESPONSE_HANDLER = "MAMBU_RESPONSE_HANDLER"
    MAMBU_LOAN_ORIGINATION = "MAMBU_LOAN_ORIGINATION"
    PAYMENT_MAMBU_RESPONSE = "PAYMENT_MAMBU_RESPONSE"
    CLIENT_BY_PARENT = "CLIENT_BY_PARENT"
    CONTRACT_LENDING = "CONTRACT_LENDING"
    PAYMENT_MAMBU_REQUEST = "PAYMENT_MAMBU_REQUEST"
