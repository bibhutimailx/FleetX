-- Initialize the fleet management database
CREATE DATABASE IF NOT EXISTS fleet_management;

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Set timezone
SET timezone = 'UTC';

