CREATE OR REPLACE VIEW DB.SCHEMA.S6_CPDP_SERVICE_USER_SEARCH AS
select name, created_on,LAST_SUCCESS_LOGIN, PASSWORD_LAST_SET_TIME,
display_name, email,default_warehouse, default_role,has_rsa_public_key,
case when has_rsa_public_key = 'TRUE' then 'STREAMLIT'
else 'NO STREAMLIT' end Streamlit_Availability,
CASE
        when PASSWORD_LAST_SET_TIME is null then 'NEVER ROTATED'
        WHEN DATEDIFF('day', CURRENT_DATE(), PASSWORD_LAST_SET_TIME) <= 30  THEN 'CRITICAL'
        WHEN DATEDIFF('day', CURRENT_DATE(), PASSWORD_LAST_SET_TIME) <= 60  THEN 'HIGH'
        WHEN DATEDIFF('day', CURRENT_DATE(), PASSWORD_LAST_SET_TIME) <= 90  THEN 'MEDIUM'
        ELSE 'LOW'
    END AS URGENCY_LEVEL,
    'DEV' env,
    'CPDP' APPLICATION_NAME,
    case when LAST_SUCCESS_LOGIN is null then 'DISABLED'
    WHEN DATEDIFF('day', CURRENT_DATE(), LAST_SUCCESS_LOGIN) <= 90 THEN 'ACTIVE'
    ELSE '' end AS ACCOUNT_STATUS,
case when PASSWORD_LAST_SET_TIME is null then 0
else DATEDIFF('day', CURRENT_DATE(), PASSWORD_LAST_SET_TIME) end AS DAYS_UNTIL_EXPIRY  ,
CASE
        WHEN PASSWORD_LAST_SET_TIME IS NULL                                         THEN NULL
        ELSE DATEADD('day', 180, PASSWORD_LAST_SET_TIME)
    END                                                     AS RSA_EXPIRY_DATE,
-- THE KEY COLUMN: rich searchable text combining all fields into one narrative
    CONCAT_WS(' ',
        'Service user', name,
        'environment', ENV,
        'used by application', APPLICATION_NAME,
        'contact', EMAIL,
        'account status', ACCOUNT_STATUS,
        'RSA enabled', IFF(has_rsa_public_key, 'yes', 'no'),
        'created on', CAST(created_on AS VARCHAR),
        COALESCE('password last updated ' || CAST(CAST(PASSWORD_LAST_SET_TIME AS DATE) AS VARCHAR), 'password never updated'),
        COALESCE('RSA key created ' || CAST(PASSWORD_LAST_SET_TIME AS VARCHAR), 'no RSA key')
    )    AS SEARCH_TEXT
from ops.prs.users where type not in ('PERSON')
