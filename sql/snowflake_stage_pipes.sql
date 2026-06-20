-- =====================================================
-- DROP EXISTING OBJECTS
-- =====================================================

DROP PIPE IF EXISTS RAW.CUSTOMERS_PIPE;
DROP PIPE IF EXISTS RAW.PRODUCTS_PIPE;
DROP PIPE IF EXISTS RAW.ORDERS_PIPE;

DROP STAGE IF EXISTS RAW.CUSTOMERS_RAW;
DROP STAGE IF EXISTS RAW.PRODUCTS_RAW;
DROP STAGE IF EXISTS RAW.ORDERS_RAW;

DROP INTEGRATION IF EXISTS S3_INT;

-- =====================================================
-- STORAGE INTEGRATION
-- =====================================================

CREATE OR REPLACE STORAGE INTEGRATION S3_INT
TYPE = EXTERNAL_STAGE
STORAGE_PROVIDER = S3
ENABLED = TRUE
STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::775154429798:role/snowflake-s3-role'
STORAGE_ALLOWED_LOCATIONS = (
's3://jeet-project-raw-layer/'
);

-- Verify and retrieve:
-- STORAGE_AWS_IAM_USER_ARN
-- STORAGE_AWS_EXTERNAL_ID
DESC INTEGRATION S3_INT;

-- =====================================================
-- CUSTOMERS STAGE
-- =====================================================

CREATE OR REPLACE STAGE RAW.CUSTOMERS_RAW
STORAGE_INTEGRATION = S3_INT
URL = 's3://jeet-project-raw-layer/raw/customers/'
FILE_FORMAT = (
TYPE = PARQUET
);

LIST @RAW.CUSTOMERS_RAW;

-- =====================================================
-- PRODUCTS STAGE
-- =====================================================

CREATE OR REPLACE STAGE RAW.PRODUCTS_RAW
STORAGE_INTEGRATION = S3_INT
URL = 's3://jeet-project-raw-layer/raw/products/'
FILE_FORMAT = (
TYPE = PARQUET
);

LIST @RAW.PRODUCTS_RAW;

-- =====================================================
-- ORDERS STAGE
-- =====================================================

CREATE OR REPLACE STAGE RAW.ORDERS_RAW
STORAGE_INTEGRATION = S3_INT
URL = 's3://jeet-project-raw-layer/raw/orders/'
FILE_FORMAT = (
TYPE = PARQUET
);

LIST @RAW.ORDERS_RAW;

-- =====================================================
-- CUSTOMERS PIPE
-- =====================================================

CREATE OR REPLACE PIPE RAW.CUSTOMERS_PIPE
AUTO_INGEST = TRUE
AS
COPY INTO RAW.CUSTOMERS
FROM @RAW.CUSTOMERS_RAW
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

DESC PIPE RAW.CUSTOMERS_PIPE;

SELECT SYSTEM$PIPE_STATUS('RAW.CUSTOMERS_PIPE');

-- Load existing files once
ALTER PIPE RAW.CUSTOMERS_PIPE REFRESH;

-- =====================================================
-- PRODUCTS PIPE
-- =====================================================

CREATE OR REPLACE PIPE RAW.PRODUCTS_PIPE
AUTO_INGEST = TRUE
AS
COPY INTO RAW.PRODUCTS
FROM @RAW.PRODUCTS_RAW
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

DESC PIPE RAW.PRODUCTS_PIPE;

SELECT SYSTEM$PIPE_STATUS('RAW.PRODUCTS_PIPE');

-- Load existing files once
ALTER PIPE RAW.PRODUCTS_PIPE REFRESH;

-- =====================================================
-- ORDERS PIPE
-- =====================================================

CREATE OR REPLACE PIPE RAW.ORDERS_PIPE
AUTO_INGEST = TRUE
AS
COPY INTO RAW.ORDERS
FROM @RAW.ORDERS_RAW
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

DESC PIPE RAW.ORDERS_PIPE;

SELECT SYSTEM$PIPE_STATUS('RAW.ORDERS_PIPE');

-- Load existing files once
ALTER PIPE RAW.ORDERS_PIPE REFRESH;

-- =====================================================
-- VALIDATION
-- =====================================================

SELECT *
FROM RAW.CUSTOMERS;

SELECT * 
FROM RAW.PRODUCTS;

SELECT * 
FROM RAW.ORDERS;

-- =====================================================
-- PIPE HEALTH CHECK
-- =====================================================

SHOW PIPES;

SELECT SYSTEM$PIPE_STATUS('RAW.CUSTOMERS_PIPE');
SELECT SYSTEM$PIPE_STATUS('RAW.PRODUCTS_PIPE');
SELECT SYSTEM$PIPE_STATUS('RAW.ORDERS_PIPE');
