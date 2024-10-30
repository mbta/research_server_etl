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
-- CREATE INIT GTFS SCHEMA --
-- ****************************************** --

CREATE SCHEMA gtfs;

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS postgis_raster WITH SCHEMA public;

CREATE FUNCTION gtfs.drop_feed(startdate text, enddate text) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN 
EXECUTE 'DROP TABLE IF EXISTS gtfs.agency_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.calendar_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.calendar_attributes_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.calendar_dates_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.checkpoints_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.directions_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.facilities_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.facilities_properties_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.fare_attributes_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.fare_rules_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.frequencies_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.levels_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.lines_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.multi_route_trips_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.pathways_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.route_patterns_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.routes_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.shapes_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.shapes_geog_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.stop_in_pattern_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.stop_times_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.stops_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.stops_geog_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.transfers_' || startdate || '_' || enddate;
EXECUTE 'DROP TABLE IF EXISTS gtfs.trips_' || startdate || '_' || enddate;
END;$$;


SET default_tablespace = '';

CREATE TABLE gtfs.agency (
    agency_id text NOT NULL,
    agency_name text NOT NULL,
    agency_url text NOT NULL,
    agency_timezone text NOT NULL,
    agency_lang text,
    agency_phone text,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT agency_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT agency_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.calendar (
    service_id text NOT NULL,
    monday integer NOT NULL,
    tuesday integer NOT NULL,
    wednesday integer NOT NULL,
    thursday integer NOT NULL,
    friday integer NOT NULL,
    saturday integer NOT NULL,
    sunday integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT calendar_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT calendar_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.calendar_attributes (
    service_id text NOT NULL,
    service_description text,
    service_schedule_name text,
    service_schedule_type text,
    service_schedule_typicality integer,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT calendar_attributes_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT calendar_attributes_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.calendar_dates (
    service_id text NOT NULL,
    date date NOT NULL,
    exception_type integer NOT NULL,
    holiday_name text,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT calendar_dates_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT calendar_dates_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.checkpoints (
    checkpoint_id text NOT NULL,
    checkpoint_name text,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT checkpoints_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT checkpoints_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.directions (
    route_id text NOT NULL,
    direction_id integer NOT NULL,
    direction text,
    direction_destination text,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT directions_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT directions_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.facilities (
    facility_id text NOT NULL,
    facility_code text,
    facility_class integer,
    facility_type text,
    stop_id text,
    facility_short_name text,
    facility_long_name text,
    facility_desc text,
    facility_lat double precision,
    facility_lon double precision,
    wheelchair_facility integer,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT facilities_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT facilities_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.facilities_properties (
    facility_id text NOT NULL,
    property_id text NOT NULL,
    value text,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT facilities_properties_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT facilities_properties_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.feed_info (
    feed_publisher_name text NOT NULL,
    feed_publisher_url text NOT NULL,
    feed_lang text NOT NULL,
    feed_start_date date NOT NULL,
    feed_end_date date NOT NULL,
    feed_version text,
    feed_contact_email text,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    creation_timestamp timestamp with time zone NOT NULL,
    etag text
);

CREATE TABLE gtfs.levels (
    level_id text NOT NULL,
    level_index integer,
    level_name text,
    level_elevation text,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT levels_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT levels_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.lines (
    line_id text NOT NULL,
    line_short_name text,
    line_long_name text,
    line_desc text,
    line_url text,
    line_color text,
    line_text_color text,
    line_sort_order integer,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT lines_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT lines_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.multi_route_trips (
    added_route_id text NOT NULL,
    trip_id text NOT NULL,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT multi_route_trips_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT multi_route_trips_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.pathways (
    pathway_id text NOT NULL,
    from_stop_id text NOT NULL,
    to_stop_id text NOT NULL,
    facility_id text,
    pathway_mode integer,
    pathway_type integer,
    traversal_time integer,
    wheelchair_traversal_time integer,
    ramp_slope integer,
    stair_count integer,
    pathway_name text,
    pathway_code text,
    signposted_as text,
    instructions text,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT pathways_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT pathways_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.route_patterns (
    route_pattern_id text NOT NULL,
    route_id text NOT NULL,
    direction_id integer NOT NULL,
    route_pattern_name text,
    route_pattern_time_desc text,
    route_pattern_typicality integer,
    route_pattern_sort_order integer,
    representative_trip_id text NOT NULL,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT route_patterns_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT route_patterns_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.routes (
    route_id text NOT NULL,
    agency_id text,
    route_short_name text,
    route_long_name text,
    route_desc text,
    route_type integer NOT NULL,
    route_url text,
    route_color text,
    route_text_color text,
    route_sort_order integer,
    route_fare_class text,
    line_id text,
    listed_route text,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT routes_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT routes_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.shapes (
    shape_id text NOT NULL,
    shape_pt_lat double precision NOT NULL,
    shape_pt_lon double precision NOT NULL,
    shape_pt_sequence integer NOT NULL,
    shape_dist_traveled double precision,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT shapes_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT shapes_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.shapes_geog (
    shape_id text NOT NULL,
    shape public.geometry(LineString,4326),
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT shapes_geog_shape_check CHECK (((public.geometrytype(shape) = 'LINESTRING'::text) OR (shape IS NULL))),
    CONSTRAINT shapes_geog_shape_check1 CHECK ((public.st_srid(shape) = 4326)),
    CONSTRAINT shapes_geog_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT shapes_geog_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.stop_in_pattern (
    shape_id text NOT NULL,
    stop_sequence integer NOT NULL,
    stop_id text NOT NULL,
    cumulative_distance integer,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT stop_in_pattern_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT stop_in_pattern_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.stop_times (
    trip_id text NOT NULL,
    arrival_time interval NOT NULL,
    departure_time interval NOT NULL,
    stop_id text NOT NULL,
    stop_sequence integer NOT NULL,
    stop_headsign text,
    pickup_type integer,
    drop_off_type integer,
    timepoint text,
    checkpoint_id text,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT stop_times_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT stop_times_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.stops (
    stop_id text NOT NULL,
    stop_code text,
    stop_name text NOT NULL,
    stop_desc text,
    stop_lat double precision,
    stop_lon double precision,
    zone_id text,
    stop_address text,
    stop_url text,
    level_id text,
    location_type integer,
    parent_station text,
    stop_timezone text,
    wheelchair_boarding integer,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT stops_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT stops_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.stops_geog (
    stop_id text NOT NULL,
    parent_station text,
    geog_latlon public.geography(Point,4326),
    geom public.geometry,
    easting integer,
    northing integer,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT stops_geog_geom_check CHECK ((public.st_ndims(geom) = 2)),
    CONSTRAINT stops_geog_geom_check1 CHECK (((public.geometrytype(geom) = 'POINT'::text) OR (geom IS NULL))),
    CONSTRAINT stops_geog_geom_check2 CHECK ((public.st_srid(geom) = 4326)),
    CONSTRAINT stops_geog_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT stops_geog_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.transfers (
    from_stop_id text NOT NULL,
    to_stop_id text NOT NULL,
    transfer_type integer NOT NULL,
    min_transfer_time integer,
    min_walk_time integer,
    min_wheelchair_time integer,
    suggested_buffer_time integer,
    wheelchair_transfer integer,
    -- from_trip_id text,
    -- to_trip_id text,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT transfers_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT transfers_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

CREATE TABLE gtfs.trips (
    route_id text NOT NULL,
    service_id text NOT NULL,
    trip_id text NOT NULL,
    trip_headsign text,
    trip_short_name text,
    direction_id integer,
    block_id text,
    shape_id text,
    wheelchair_accessible integer,
    trip_route_type integer,
    route_pattern_id text,
    bikes_allowed integer,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    CONSTRAINT trips_valid_end_date_check CHECK ((valid_end_date = '1900-01-01'::date)) NO INHERIT,
    CONSTRAINT trips_valid_start_date_check CHECK ((valid_start_date = '1900-01-01'::date)) NO INHERIT
);

ALTER TABLE ONLY gtfs.agency
    ADD CONSTRAINT agency_pkey PRIMARY KEY (valid_start_date, valid_end_date, agency_id);

ALTER TABLE ONLY gtfs.calendar_dates
    ADD CONSTRAINT calendar_dates_pkey PRIMARY KEY (valid_start_date, valid_end_date, service_id, date);

ALTER TABLE ONLY gtfs.calendar
    ADD CONSTRAINT calendar_pkey PRIMARY KEY (valid_start_date, valid_end_date, service_id);

ALTER TABLE ONLY gtfs.checkpoints
    ADD CONSTRAINT checkpoints_pkey PRIMARY KEY (valid_start_date, valid_end_date, checkpoint_id);

ALTER TABLE ONLY gtfs.directions
    ADD CONSTRAINT directions_pkey PRIMARY KEY (valid_start_date, valid_end_date, route_id, direction_id);

ALTER TABLE ONLY gtfs.facilities
    ADD CONSTRAINT facilities_pkey PRIMARY KEY (valid_start_date, valid_end_date, facility_id);

ALTER TABLE ONLY gtfs.feed_info
    ADD CONSTRAINT feed_info_feed_start_date_feed_end_date_key UNIQUE (feed_start_date, feed_end_date);

ALTER TABLE ONLY gtfs.feed_info
    ADD CONSTRAINT feed_info_pkey PRIMARY KEY (valid_start_date, valid_end_date);

ALTER TABLE ONLY gtfs.levels
    ADD CONSTRAINT levels_pkey PRIMARY KEY (valid_start_date, valid_end_date, level_id);

ALTER TABLE ONLY gtfs.lines
    ADD CONSTRAINT lines_pkey PRIMARY KEY (valid_start_date, valid_end_date, line_id);

ALTER TABLE ONLY gtfs.multi_route_trips
    ADD CONSTRAINT multi_route_trips_pkey PRIMARY KEY (valid_start_date, valid_end_date, added_route_id, trip_id);

ALTER TABLE ONLY gtfs.pathways
    ADD CONSTRAINT pathways_pkey PRIMARY KEY (valid_start_date, valid_end_date, pathway_id);

ALTER TABLE ONLY gtfs.route_patterns
    ADD CONSTRAINT route_patterns_pkey PRIMARY KEY (valid_start_date, valid_end_date, route_pattern_id);

ALTER TABLE ONLY gtfs.routes
    ADD CONSTRAINT routes_pkey PRIMARY KEY (valid_start_date, valid_end_date, route_id);

ALTER TABLE ONLY gtfs.shapes_geog
    ADD CONSTRAINT shapes_geog_pkey PRIMARY KEY (valid_start_date, valid_end_date, shape_id);

ALTER TABLE ONLY gtfs.shapes
    ADD CONSTRAINT shapes_pkey PRIMARY KEY (valid_start_date, valid_end_date, shape_id, shape_pt_sequence);

ALTER TABLE ONLY gtfs.stop_in_pattern
    ADD CONSTRAINT stop_in_pattern_pkey PRIMARY KEY (valid_start_date, valid_end_date, shape_id, stop_sequence);

ALTER TABLE ONLY gtfs.stop_times
    ADD CONSTRAINT stop_times_pkey PRIMARY KEY (valid_start_date, valid_end_date, trip_id, stop_sequence);

ALTER TABLE ONLY gtfs.stops_geog
    ADD CONSTRAINT stops_geog_pkey PRIMARY KEY (valid_start_date, valid_end_date, stop_id);

ALTER TABLE ONLY gtfs.stops
    ADD CONSTRAINT stops_pkey PRIMARY KEY (valid_start_date, valid_end_date, stop_id);

ALTER TABLE ONLY gtfs.trips
    ADD CONSTRAINT trips_pkey PRIMARY KEY (valid_start_date, valid_end_date, route_id);

-- ****************************************** --
-- END INIT GTFS SCHEMA --
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
    , account_key TEXT
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