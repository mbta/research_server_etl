--
-- PostgreSQL database dump
--

-- Dumped from database version 10.16 (Ubuntu 10.16-0ubuntu0.18.04.1)
-- Dumped by pg_dump version 13.11 (Debian 13.11-0+deb11u1)

-- Started on 2023-10-03 12:06:21 EDT

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- ****************************************** --
-- CREATE INIT SB_API SCHEMA --
-- ****************************************** --

CREATE SCHEMA sb_api;

CREATE TABLE sb_api.v_validation_taps (
    job_id BIGINT
    , identity_value BIGINT
    , backofficetxnid BIGINT
    , businessentityid INTEGER
    , deviceid TEXT
    , deviceclassid TEXT
    , mediumid TEXT
    , tat TEXT
    , agentid TEXT
    , lineid TEXT
    , stoppointid TEXT
    , transactiontimestamp TIMESTAMP
    , receivedat TIMESTAMP
    , onlineprocessingstatus TEXT
    , denialreason TEXT
    , authorizationresult TEXT
    , valid TEXT
    , entryexittype TEXT
    , routeid TEXT
    , servicepatternid TEXT
    , deviceservicemode TEXT
    , servicecategory TEXT
    , transactionsubtype TEXT
    , zoneid TEXT
    , devicetariffversionid TEXT
    , txnseqno BIGINT
    , transactionreference TEXT
) PARTITION BY RANGE (transactiontimestamp);

CREATE INDEX ON sb_api.v_validation_taps (transactiontimestamp);

CREATE TABLE sb_api.v_mainshift (
    job_id BIGINT
    , identity_value BIGINT
    , deviceclassid TEXT
    , deviceid TEXT
    , uniquemsid BIGINT
    , mainshiftno BIGINT
    , startcreadate TIMESTAMP
    , endcreadate TIMESTAMP
    , starteventsequno BIGINT
    , endeventsequno BIGINT
    , polldate TIMESTAMP
    , dbwritecmddate TIMESTAMP
    , proceedingtype BIGINT
    , locationid BIGINT
    , serviceno BIGINT
    , vehicleno BIGINT
    , routeno BIGINT
    , tourno BIGINT
    , tariffversion BIGINT
    , tarifflocationid BIGINT
    , locationtype BIGINT
    , vendorno BIGINT
    , shifttype BIGINT
    , modulno BIGINT
    , modulusertype BIGINT
    , sellingrrid BIGINT
    , shiftpiece BIGINT
    , shiftminuspiece BIGINT
    , shiftoutamount BIGINT
    , shiftminusamount BIGINT
    , creditamount BIGINT
    , cashless BIGINT
    , lastsalesshiftno BIGINT
    , mainshiftclosestatus BIGINT
    , jobid TEXT
    , jobsequid BIGINT
    , bankcode BIGINT
    , bankaccount BIGINT
    , insertdate TIMESTAMP
    , testflag BIGINT
    , auditstatus BIGINT
    , auditorsystemid TEXT
    , statusdatetime TIMESTAMP
    , jobstate BIGINT
    , soldcurrency BIGINT
    , currency BIGINT
    , shiftchangereasonstart BIGINT
    , shiftchangereasonend BIGINT
    , sbserialnumber BIGINT
    , baseplateid TEXT
    , soldforcompany BIGINT
) PARTITION BY RANGE (insertdate);

CREATE INDEX ON sb_api.v_mainshift (insertdate);

CREATE TABLE sb_api.v_trips (
    job_id BIGINT
    , identity_value BIGINT
    , tripid BIGINT
    , tripversion BIGINT
    , tripstart TIMESTAMP
    , tripend TIMESTAMP
    , versioncreationtimestamp TIMESTAMP
    , tat TEXT
    , legid TEXT
    , businessentityid INTEGER
    , transportmode TEXT
    , transportsubmode TEXT
    , tariffversionid TEXT
    , appliedproductinstanceid TEXT
    , appliedproducttemplateid TEXT
    , appliedmetric TEXT
    , appliedunit TEXT
    , appliedvalue BIGINT
    , backofficetxnid BIGINT
    , taptype TEXT
    , deviceid TEXT
    , deviceclassid TEXT
    , stoppointid TEXT
    , mediumid TEXT
    , transactiontimestamp TIMESTAMP
) PARTITION BY RANGE (transactiontimestamp);

CREATE INDEX ON sb_api.v_trips (transactiontimestamp);

CREATE TABLE sb_api.v_sales_txns (
    job_id BIGINT
    , identity_value BIGINT
    , salestxnid TEXT
    , spit TEXT
    , tariffversionid TEXT
    , refundfeeamount TEXT
    , refundfeecurrency TEXT
    , refundreason TEXT
    , packagetemplateid TEXT
    , tat TEXT
    , packageseq INTEGER
    , productseq INTEGER
    , producttemplateid TEXT
    , itemtype TEXT
    , itemamount INTEGER
    , itemcurrency TEXT
    , paymentseq INTEGER
    , paymentmethod TEXT
    , paymentprocessed TEXT
    , paymentamount INTEGER
    , paymentcurrency TEXT
    , billingmode TEXT
    , purchasercustomerid TEXT
    , purchaserbillingprofileid TEXT
    , transactiontimestamp TIMESTAMP
    , saleschanneltype TEXT
    , clientlineid TEXT
    , clientservicepatternid TEXT
    , clientstoppointid TEXT
    , clientzoneid TEXT
    , deviceid TEXT
    , deviceclassid TEXT
    , businessentityid INTEGER
    , agentid TEXT
    , salestransactiontype TEXT
    , servicereferenceid TEXT
    , vouchercode TEXT
    , voucherredeemedamount INTEGER
    , vouchercurrency TEXT
) PARTITION BY RANGE (transactiontimestamp);

CREATE INDEX ON sb_api.v_sales_txns (transactiontimestamp);

CREATE TABLE sb_api.v_media (
    job_id BIGINT
    , identity_value BIGINT
    , mediumid TEXT
    , idtype BIGINT
    , mediumstatus TEXT
    , tat TEXT
    , expirationtimestamp TIMESTAMP
    , statuschangetimestamp TIMESTAMP
) PARTITION BY RANGE (statuschangetimestamp);

CREATE INDEX ON sb_api.v_media (statuschangetimestamp);

CREATE TABLE sb_api.v_shiftevent (
    job_id BIGINT
    , identity_value BIGINT
    , deviceclassid TEXT
    , deviceid TEXT
    , uniquemsid BIGINT
    , eventsequno BIGINT
    , creadate TIMESTAMP
    , salesshiftno BIGINT
    , eventtype BIGINT
    , proceedingtype BIGINT
    , locationname TEXT
    , vendorno BIGINT
    , eventcode BIGINT
    , outofservstatus BIGINT
    , devicestatus BIGINT
    , eventstatus BIGINT
    , assemblyno BIGINT
    , subassemblyno BIGINT
    , amount BIGINT
    , numberofpieces BIGINT
    , employeeno BIGINT
    , assembserno BIGINT
    , actioncounter BIGINT
    , vehicleno BIGINT
    , routeno BIGINT
    , tourno BIGINT
    , tariffversion BIGINT
    , tarifflocationid BIGINT
    , locationtype BIGINT
    , partitioningdate TIMESTAMP
) PARTITION BY RANGE (creadate);

CREATE INDEX ON sb_api.v_shiftevent (creadate);

CREATE TABLE sb_api.v_person (
    job_id BIGINT
    , identity_value BIGINT
    , personid BIGINT
    , parentid BIGINT
    , addressid BIGINT
    , employeenumber BIGINT
    , iscommercial BIGINT
    , organization TEXT
    , departement TEXT
    , info1 TEXT
    , info2 TEXT
    , additionalinfo TEXT
    , lastlogontry TIMESTAMP
    , nofailedlogtries BIGINT
    , admintype BIGINT
    , datachangeid BIGINT
);

CREATE TABLE sb_api.v_tvmtable (
    job_id BIGINT
    , identity_value BIGINT
    , deviceclassid TEXT
    , tvmid TEXT
    , tvmabbreviation TEXT
    , tvmlocation1 TEXT
    , tvmlocation2 TEXT
    , tvmpostalcode TEXT
    , tvmgroupref BIGINT
    , tvmtarifflocationid BIGINT
    , tvmtariffzoneid BIGINT
    , tvmtarversiongroupid BIGINT
    , tvmapltarversiongroupid BIGINT
    , tvmtechversiongroupid BIGINT
    , tvmswversiongroupid BIGINT
    , tvminstanceid BIGINT
    , tvmnetaddr TEXT
    , tvmnetsubaddr TEXT
    , tvmrouteraddr TEXT
    , companyid BIGINT
    , tvmlicense1 TEXT
    , tvmlicense2 TEXT
    , tvmphonenumber TEXT
    , tvmfepgroupref BIGINT
    , tvmnetconfgroupref BIGINT
    , tvmnetmode BIGINT
    , defaultstartgroupid BIGINT
    , defaultdestgroupid BIGINT
    , routeid TEXT
    , multimediagroupid BIGINT
    , versionid BIGINT
    , bankcode BIGINT
    , bankaccount BIGINT
    , serialno TEXT
    , balancegroupid BIGINT
    , fieldstate BIGINT
    , parametergroupid BIGINT
    , tvmmanualversiongroupid BIGINT
    , domainname TEXT
    , fieldsubstate BIGINT
    , tvmcomment TEXT
);

CREATE TABLE sb_api.v_cashless_payments (
    job_id BIGINT
    , identity_value BIGINT
    , merchantid TEXT
    , chargeid BIGINT
    , actionindex BIGINT
    , actiontype TEXT
    , capture BOOLEAN
    , tapdebtrecovery BOOLEAN
    , actionresult TEXT
    , responsereferencecode TEXT
    , paymentprovidererror TEXT
    , requesttimestamp TIMESTAMP
    , responsetimestamp TIMESTAMP
    , tenant TEXT
    , terminalid TEXT
    , mediumid TEXT
    , paymenttype TEXT
    , paymentcardtype TEXT
    , carddataentrymode TEXT
    , transitmode BOOLEAN
    , cardbrand TEXT
    , cardbin TEXT
    , cardmaskedpan TEXT
    , paymentaccountreference TEXT
    , servicereferenceid TEXT
    , requestreferenceid TEXT
    , responsetransactionnumber TEXT
    , avsresponsecode TEXT
    , cvvresponsecode TEXT
    , amount BIGINT
    , currency TEXT
    , cardholderauthorizationmethod TEXT
) PARTITION BY RANGE (requesttimestamp);

CREATE INDEX ON sb_api.v_cashless_payments (requesttimestamp);

CREATE TABLE sb_api.v_inspections (
    job_id BIGINT
    , identity_value BIGINT
    , inspectionid BIGINT
    , inquirytimestamp TIMESTAMP
    , businessentityid BIGINT
    , deviceid TEXT
    , deviceclassid TEXT
    , mediumid TEXT
    , onlineprocessingstatus BOOLEAN
    , preresult TEXT
    , result TEXT
    , overridereason TEXT
    , inspectionstoppointid TEXT
    , lineid TEXT
    , servicepatternid TEXT
) PARTITION BY RANGE (inquirytimestamp);

CREATE INDEX ON sb_api.v_inspections (inquirytimestamp);

-- ****************************************** --
-- END INIT SB_API SCHEMA --
-- ****************************************** --

-- ****************************************** --
-- CREATE INIT ODX2 SCHEMA --
-- ****************************************** --

CREATE SCHEMA odx2;

CREATE TABLE odx2.fare_action (
    action_key SMALLINT PRIMARY KEY
    , action_name TEXT
    , action_desc TEXT
);

CREATE TABLE odx2.fare_medium (
    fare_med_key SMALLINT PRIMARY KEY
    , fare_med_name TEXT
    , fare_med_desc TEXT
);

CREATE TABLE odx2.fare_product (
    fare_prod_id TEXT PRIMARY KEY
    , fare_prod_name TEXT
    , fare_prod_desc TEXT
    , category_key SMALLINT
    , rider_type_key SMALLINT
    , days_valid SMALLINT
    , temporal_validity TEXT
);

CREATE TABLE odx2.fare_product_category (
    category_key SMALLINT PRIMARY KEY
    , category_name TEXT
    , category_desc TEXT
);

CREATE TABLE odx2.fare_transaction (
    txn_key BIGINT
    , svc_date DATE
    , card TEXT
    , txn_time TIMESTAMP NOT NULL
    , action_key SMALLINT NOT NULL
    , device_id TEXT NOT NULL
    , txn_seq INT NOT NULL
    , fare_med_key SMALLINT
    , fare_prod_id TEXT
    , amount INTEGER
    , sv_balance INTEGER
    , ride_balance SMALLINT
    , account_id TEXT
    , xfer_to BOOLEAN
    , vehicle_id TEXT
    , route_id TEXT
    , dir_id TEXT
    , pattern_id TEXT
    , trip_id TEXT
    , place_id TEXT
    , lat DOUBLE PRECISION
    , lon DOUBLE PRECISION
    , canceled BOOLEAN NOT NULL
    , insert_dt TIMESTAMP NOT NULL
) PARTITION BY RANGE (svc_date);

CREATE INDEX ON odx2.fare_transaction (svc_date);

CREATE TABLE odx2.fleet (
    fleet_key smallint NOT NULL,
    fleet_name text NOT NULL,
    operator_id text NOT NULL
);

CREATE TABLE odx2.od_code (
    od_code smallint NOT NULL,
    od_code_name text,
    od_code_desc text
);

CREATE TABLE odx2.pattern (
    pattern_id text PRIMARY KEY,
    route_id text NOT NULL,
    gtfs_dir smallint,
    dir_id text,
    pattern_name text,
    in_service boolean,
    CONSTRAINT pattern_gtfs_dir_check CHECK ((gtfs_dir = ANY (ARRAY[0, 1])))
);

CREATE TABLE odx2.pattern_flow (
    svc_date date NOT NULL,
    pattern_id text NOT NULL,
    hhr interval NOT NULL,
    trip_hhr interval NOT NULL,
    stop_seq smallint NOT NULL,
    ons real,
    offs real,
    flow_out real,
    insert_dt timestamp with time zone NOT NULL
);

CREATE TABLE odx2.pattern_stop (
    pattern_id text NOT NULL,
    stop_seq integer NOT NULL,
    stop_id text NOT NULL,
    meters double precision
);

CREATE TABLE odx2.ride (
    stage_key bigint NOT NULL,
    ride_seq smallint NOT NULL,
    svc_date date NOT NULL,
    start_visit_key bigint,
    end_visit_key bigint,
    insert_dt timestamp with time zone NOT NULL
);

CREATE TABLE odx2.rider_type (
    rider_type_key SMALLINT PRIMARY KEY
    , rider_type_name TEXT
    , rider_type_desc TEXT
);

CREATE TABLE odx2.stage (
    stage_key bigint NOT NULL,
    svc_date date NOT NULL,
    card text,
    jny_seq smallint NOT NULL,
    stage_seq smallint NOT NULL,
    origin text,
    destination text,
    o_time timestamp with time zone,
    d_time timestamp with time zone,
    num_riders smallint NOT NULL,
    o_txn_key bigint,
    d_txn_key bigint,
    o_code smallint NOT NULL,
    d_code smallint NOT NULL,
    x_code smallint NOT NULL,
    insert_dt timestamp with time zone NOT NULL
);

CREATE TABLE odx2.trip (
    trip_key bigint NOT NULL,
    svc_date date NOT NULL,
    vehicle_day_key bigint NOT NULL,
    in_service boolean,
    trip_id text,
    sched_trip text,
    num_visits integer NOT NULL,
    route_id text,
    dir_id text,
    pattern_id text,
    insert_dt timestamp with time zone NOT NULL
);

CREATE TABLE odx2.vehicle_day (
    vehicle_day_key bigint NOT NULL,
    svc_date date NOT NULL,
    vehicle_id text,
    fleet_key smallint NOT NULL,
    num_cars smallint,
    insert_dt timestamp with time zone NOT NULL
);

CREATE TABLE odx2.visit (
    visit_key bigint NOT NULL,
    svc_date date NOT NULL,
    vehicle_day_key bigint NOT NULL,
    seq_in_day integer NOT NULL,
    arrival timestamp with time zone,
    door_open timestamp with time zone,
    door_close timestamp with time zone,
    departure timestamp with time zone,
    trip_key bigint NOT NULL,
    seq_in_trip integer NOT NULL,
    seq_in_pattern integer,
    scheduled boolean,
    stop_id text,
    lat double precision,
    lon double precision,
    ons real,
    offs real,
    load_out real,
    apc_ons real,
    apc_offs real,
    apc_load_out real,
    insert_dt timestamp with time zone NOT NULL
);

CREATE TABLE odx2.xfer_code (
    xfer_code smallint NOT NULL,
    xfer_code_name text,
    xfer_code_desc text
);

-- ****************************************** --
-- END INIT ODX2 SCHEMA --
-- ****************************************** --


-- ****************************************** --
-- CREATE INIT AFC SCHEMA --
-- ****************************************** --

CREATE SCHEMA afc;

CREATE TABLE afc.faregate (
    trxtime timestamp without time zone,
    servicedate date,
    deviceclassid integer,
    deviceid integer,
    uniquemsid integer,
    eventsequno integer,
    tariffversion integer, 
    tarifflocationid integer,
    unplanned boolean,
    eventcode integer,
    inserted timestamp without time zone
) PARTITION BY RANGE (servicedate);

CREATE INDEX ON afc.faregate (servicedate);

CREATE TABLE afc.ridership (
    deviceclassid integer,
    deviceid integer,
    uniquemsid integer,
    salestransactionno integer,
    sequenceno integer,
    trxtime timestamp without time zone,
    servicedate date, 
    branchlineid character varying(50),
    fareoptamount integer,
    tariffversion integer, 
    articleno integer,
    card character varying(50),
    ticketstocktype integer,
    tvmtarifflocationid integer,
    movementtype integer,
    bookcanc integer,
    correctioncounter bit(1),
    correctionflag bit(1) DEFAULT 0::bit NOT NULL,
    tempbooking bit(1) NOT NULL,
    testsaleflag bit(1),
    inserted timestamp without time zone
) PARTITION BY RANGE (servicedate);

CREATE INDEX ON afc.ridership (servicedate);


CREATE TABLE afc.deviceclass (
    deviceclassid integer PRIMARY KEY,
    balancegroupid integer,
    deviceclasstype integer,
    tvmtarversiongroupid integer,
    tvmapltarversiongroupid integer,
    tvmtechversiongroupid integer,
    tvmswversiongroupid integer,
    description character varying(50),
    testflag bit(1) NOT NULL,
    usernew character varying(30),
    timenew timestamp without time zone,
    userchange character varying(30),
    timechange timestamp without time zone,
    typeoftariffdownloaddata integer,
    parametergroupid integer
);

CREATE TABLE afc.event (
    eventcode integer PRIMARY KEY,
    eventdesc character varying(15),
    eventtxt character varying(80),
    eventgroupref integer,
    display bit(1),
    logging bit(1),
    alarm bit(1),
    sendevent bit(1),
    usernew character varying(25),
    timenew timestamp without time zone,
    userchange character varying(25),
    timechange timestamp without time zone
);

CREATE TABLE afc.eventgroup (
    eventgroupref smallint PRIMARY KEY,
    eventgroupdesc character varying(50),
    usernew character varying(25),
    timenew timestamp without time zone,
    userchange character varying(25),
    timechange timestamp without time zone
);

CREATE TABLE afc.holiday (
    versionid integer NOT NULL,
    datehour timestamp without time zone NOT NULL,
    holidayclass integer,
    description character varying(120),
    usernew character varying(25) NOT NULL,
    timenew timestamp without time zone NOT NULL,
    userchange character varying(25),
    timechange timestamp without time zone
);

CREATE TABLE afc.mbta_weekend_service (
    servicehour timestamp without time zone,
    servicedesc character varying(120),
    servicetype integer,
    dateinserted timestamp without time zone
);

CREATE TABLE afc.routes (
    routeid integer PRIMARY KEY,
    description character varying(120) NOT NULL,
    versionid integer,
    multimediagroupid integer,
    usernew character varying(25),
    timenew timestamp without time zone,
    userchange character varying(25),
    timechange timestamp without time zone
);

CREATE TABLE afc.tariffversions (
    versionid integer PRIMARY KEY,
    validitystarttime timestamp without time zone,
    validityendtime timestamp without time zone,
    railroadid integer,
    description character varying(120),
    status integer,
    theovertakerflag integer,
    usernew character varying(25),
    timenew timestamp without time zone,
    userchange character varying(25),
    timechange timestamp without time zone,
    type smallint
);

CREATE TABLE afc.tickettype (
    versionid smallint NOT NULL,
    tickettypeid integer NOT NULL,
    summary integer,
    type integer,
    amount integer,
    balamt1 integer,
    balamt2 integer,
    farecalculationruleid integer,
    multimediagroupid integer,
    statetaxid integer,
    sendonlevt integer,
    svcproviderid integer,
    validityid integer,
    genderinput integer,
    description character varying(120),
    param1 integer,
    param2 integer,
    param3 integer,
    param4 integer,
    param5 integer,
    param6 integer,
    param7 integer,
    param8 integer,
    param9 character varying(15),
    param10 character varying(15),
    usernew character varying(25),
    timenew timestamp without time zone,
    userchange character varying(15),
    timechange timestamp without time zone,
    ticketmembergroupid integer,
    externalid character varying(15)
);

CREATE TABLE afc.tvmstation (
    stationid integer PRIMARY KEY,
    nameshort character varying(50),
    namelong character varying(120),
    name character varying(120),
    town character varying(50),
    tariffproperty integer,
    tariffzone integer,
    usernew character varying(25),
    timenew timestamp without time zone,
    userchange character varying(15),
    timechange timestamp without time zone,
    companyid integer,
    graphickey integer,
    stationtype integer,
    externalid smallint
);

CREATE TABLE afc.tvmtable (
    deviceclassid integer NOT NULL,
    deviceid integer NOT NULL,
    balancegroupid integer,
    tvmabbreviation character varying(12) NOT NULL,
    tvmlocation1 character varying(120),
    tvmlocation2 character varying(120),
    tvmpostalcode character varying(10),
    tvmgroupref integer NOT NULL,
    locationid integer NOT NULL,
    tvmtariffzoneid integer,
    tvmtarversiongroupid integer,
    tvmapltarversiongroupid integer,
    tvmtechversiongroupid integer,
    tvmswversiongroupid integer,
    tvminstanceid integer,
    tvmnetaddr character varying(15),
    tvmnetsubaddr character varying(15),
    tvmrouteraddr character varying(15),
    companyid integer,
    tvmlicense1 character varying(30),
    tvmlicense2 character varying(30),
    tvmphonenumber character varying(15),
    tvmfepgroupref integer,
    tvmnetconfgroupref integer,
    tvmnetmode integer NOT NULL,
    graphickey integer,
    defaultdestgroupid integer,
    routeid integer NOT NULL,
    defaultstartgroupid integer,
    versionid integer,
    bankcode bigint,
    bankaccount bigint,
    multimediagroupid integer,
    reserved4 bigint,
    reserved5 bigint,
    reserved6 bigint,
    reserved7 bigint,
    reserved8 bigint,
    reserved9 bigint,
    reserved3 bigint,
    reserved2 bigint,
    reserved1 bigint,
    serialno integer,
    fieldstate integer,
    usernew character varying(20),
    timenew timestamp without time zone,
    userchange character varying(20),
    timechange timestamp without time zone,
    parametergroupid integer
);


-- ****************************************** --
-- END INIT AFC SCHEMA --
-- ****************************************** --


-- ****************************************** --
-- CREATE INIT GITHUB ACTIONS SCHEMA --
-- ****************************************** --

CREATE SCHEMA ridership;

CREATE TABLE ridership.tableau_r (
    servicedate date,
    halfhour timestamp without time zone,
    locationid integer,
    stationname character varying,
    route_or_line character varying(20),
    noninteraction_type character varying(20),
    ungated_type character varying(20),
    rawtaps_split numeric
);


CREATE SCHEMA surveys;

CREATE TABLE surveys.dashboard_survey_result_archive (
    survey_date date,
    survey_name character varying(100),
    question_id integer,
    response_type_id integer,
    response_total integer,
    response_1_percent numeric(10,10),
    response_2_percent numeric(10,10),
    response_3_percent numeric(10,10),
    response_4_percent numeric(10,10),
    response_5_percent numeric(10,10),
    response_6_percent numeric(10,10),
    response_7_percent numeric(10,10),
    average_rating numeric(10,2),
    survey_id integer NOT NULL,
    archive_time timestamp with time zone NOT NULL
);

ALTER TABLE surveys.dashboard_survey_result_archive ALTER COLUMN survey_id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME surveys.dashboard_survey_result_archive_survey_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

CREATE TABLE surveys.dashboard_survey_response_type_archive (
    response_type_id integer,
    response_1_text character varying(40),
    response_2_text character varying(40),
    response_3_text character varying(40),
    response_4_text character varying(40),
    response_5_text character varying(40),
    response_6_text character varying(40),
    response_7_text character varying(40),
    archive_time timestamp with time zone NOT NULL
);

CREATE TABLE surveys.dashboard_survey_questions_archive (
    question_id integer,
    question_number integer,
    question_group character varying(100),
    question_description character varying(500),
    visible character varying(1),
    archive_time timestamp with time zone
);

CREATE TABLE surveys.csat (
        survey_date DATE,
        survey_name VARCHAR(255),
        question_description TEXT,
        response_total INTEGER,
        response_1_text VARCHAR(255),
        response_1_percent FLOAT,
        response_2_text VARCHAR(255),
        response_2_percent FLOAT,
        response_3_text VARCHAR(255),
        response_3_percent FLOAT,
        response_4_text VARCHAR(255),
        response_4_percent FLOAT,
        response_5_text VARCHAR(255),
        response_5_percent FLOAT,
        response_6_text VARCHAR(255),
        response_6_percent FLOAT,
        response_7_text VARCHAR(255),
        response_7_percent FLOAT
);

-- ****************************************** --
-- END INIT GITHUB ACTIONS SCHEMA --
-- ****************************************** --
