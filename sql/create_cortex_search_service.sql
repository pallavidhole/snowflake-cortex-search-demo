CREATE OR REPLACE CORTEX SEARCH SERVICE DB.SCHEMA.S7_CPDP_USER_SEARCH_CS
    ON SEARCH_TEXT                   -- the rich text column from the view
    ATTRIBUTES
        ENV,
        ACCOUNT_STATUS,
        has_rsa_public_key,
        URGENCY_LEVEL                  -- filter by urgency tier in the UI
    WAREHOUSE  = COMPUTE_WH
    TARGET_LAG = '1 day'
	EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0' AS
    AS (
        SELECT
            name AS SERVICE_USER_NAME,
            ENV,
            EMAIL_CONTACT,
            APPLICATION_NAME,
            ACCOUNT_STATUS,
            has_rsa_public_key,
            RSA_KEY_CREATED_DATE,
            RSA_EXPIRY_DATE,
            URGENCY_LEVEL,
            PASSWORD_LAST_SET_TIME,
            DAYS_UNTIL_EXPIRY AS PWD_DAYS_UNTIL_EXPIRY,
            created_on,
            SEARCH_TEXT
        FROM EDW_DEV.STG.S6_CPDP_SERVICE_USER_SEARCH
    );
