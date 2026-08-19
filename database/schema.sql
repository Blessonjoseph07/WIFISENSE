-- SQL DDL Script for Wi-Fi Sense Database Schema
-- Target Database: PostgreSQL 14+

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. UTILITY FUNCTIONS & TRIGGERS
-- ============================================================================

-- Automatic updated_at timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 2. CORE GEOGRAPHY & TENANT MODULE
-- ============================================================================

CREATE TYPE organization_type AS ENUM ('ELDER_CARE', 'CORPORATE');

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL UNIQUE,
    type organization_type NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE buildings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_building_per_org UNIQUE (organization_id, name)
);

CREATE TABLE floors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    floor_number INTEGER NOT NULL,
    floor_plan_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_floor_per_building UNIQUE (building_id, floor_number)
);

CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    floor_id UUID NOT NULL REFERENCES floors(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    room_type VARCHAR(50) NOT NULL, -- e.g., 'Resident Bedroom', 'Conference Room'
    capacity INTEGER NOT NULL DEFAULT 1,
    dimensions_metadata JSONB, -- stores {width_m, length_m, height_m}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_room_per_floor UNIQUE (floor_id, name)
);

-- ============================================================================
-- 3. IDENTITY & ROLE-BASED ACCESS CONTROL (RBAC)
-- ============================================================================

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Seed System Roles as specified in locked scope
INSERT INTO roles (id, name) VALUES
(1, 'System Administrator'),
(2, 'Organization Administrator'),
(3, 'Facility Manager'),
(4, 'Caregiver / Staff'),
(5, 'Corporate Facility Staff'),
(6, 'Emergency Contact / Family Member')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Prevent duplicate assignments of same role/scope combinations
    CONSTRAINT unique_user_role_scope UNIQUE (user_id, role_id, organization_id, building_id, room_id)
);

-- ============================================================================
-- 4. DEVICE & SENSING ENGINE
-- ============================================================================

CREATE TYPE device_status_type AS ENUM ('ONLINE', 'OFFLINE', 'MAINTENANCE');

CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
    mac_address VARCHAR(17) NOT NULL UNIQUE,
    device_status device_status_type NOT NULL DEFAULT 'OFFLINE',
    firmware_version VARCHAR(30),
    last_seen_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE activity_category AS ENUM ('STATUS', 'ACTIVITY', 'CRITICAL');

CREATE TABLE activity_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    category activity_category NOT NULL
);

-- Seed initial system-wide activity types
INSERT INTO activity_types (id, name, category) VALUES
(1, 'Empty', 'STATUS'),
(2, 'Presence', 'STATUS'),
(3, 'Walking', 'ACTIVITY'),
(4, 'Sitting', 'ACTIVITY'),
(5, 'Fall_Detected', 'CRITICAL')
ON CONFLICT (id) DO UPDATE SET category = EXCLUDED.category;

CREATE TABLE sensing_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    activity_type_id INTEGER NOT NULL REFERENCES activity_types(id) ON DELETE CASCADE,
    template_name VARCHAR(100) NOT NULL,
    csi_amplitude_baseline DOUBLE PRECISION[] NOT NULL,
    csi_phase_baseline DOUBLE PRECISION[] NOT NULL,
    environment_metadata JSONB, -- Stores environmental dimensions or interference properties
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sensing_events (
    id BIGSERIAL PRIMARY KEY,
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    rssi INTEGER NOT NULL,
    subcarrier_count INTEGER NOT NULL,
    raw_csi_payload_path VARCHAR(512), -- Pointer to file store (e.g. S3, MinIO)
    extracted_features JSONB NOT NULL, -- e.g. {"amplitude_variance": 0.42, "doppler_shift": 1.25}
    inferred_activity_id INTEGER NOT NULL REFERENCES activity_types(id) ON DELETE RESTRICT,
    model_confidence NUMERIC(5,4) NOT NULL CHECK (model_confidence >= 0.0 AND model_confidence <= 1.0)
);

-- ============================================================================
-- 5. ALERTS & NOTIFICATION ENGINE
-- ============================================================================

CREATE TYPE alert_severity_type AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE alert_status_type AS ENUM ('DETECTION', 'CREATED', 'NOTIFIED', 'ACKNOWLEDGED', 'RESOLVED');

CREATE TABLE alert_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    event_type_id INTEGER NOT NULL REFERENCES activity_types(id) ON DELETE CASCADE,
    alert_severity alert_severity_type NOT NULL DEFAULT 'MEDIUM',
    message_template TEXT NOT NULL, -- e.g., "Presence detected in vacant Room {room_name}"
    cooldown_period_seconds INTEGER NOT NULL DEFAULT 60,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alert_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    alert_template_id UUID NOT NULL REFERENCES alert_templates(id) ON DELETE CASCADE,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_room_alert_config UNIQUE (room_id, alert_template_id)
);

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_configuration_id UUID REFERENCES alert_configurations(id) ON DELETE SET NULL,
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    severity alert_severity_type NOT NULL,
    message TEXT NOT NULL,
    status alert_status_type NOT NULL DEFAULT 'DETECTION',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alert_acknowledgements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id UUID NOT NULL UNIQUE REFERENCES alerts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    acknowledged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    CONSTRAINT chk_resolved_after_acknowledged CHECK (resolved_at IS NULL OR resolved_at >= acknowledged_at)
);

-- ============================================================================
-- 6. INDEXES FOR PERFORMANCE & OPTIMIZATION
-- ============================================================================

-- Lookup indexes for multi-tenant tree traversal
CREATE INDEX idx_buildings_org ON buildings(organization_id);
CREATE INDEX idx_floors_building ON floors(building_id);
CREATE INDEX idx_rooms_floor ON rooms(floor_id);

-- Device MAC address index
CREATE INDEX idx_devices_room ON devices(room_id);

-- Time-series partitioning/indexing for event metrics
CREATE INDEX idx_sensing_events_room_time ON sensing_events (room_id, timestamp DESC);
CREATE INDEX idx_sensing_events_device_time ON sensing_events (device_id, timestamp DESC);

-- Alert query optimizations
CREATE INDEX idx_alerts_room_status ON alerts(room_id, status);
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);

-- RBAC scope lookup indexes
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_scope ON user_roles(organization_id, building_id, room_id);

-- ============================================================================
-- 7. ATTACH TRIGGER FOR UPDATED_AT COLUMNS
-- ============================================================================

CREATE TRIGGER trigger_update_organizations_timestamp BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_update_buildings_timestamp BEFORE UPDATE ON buildings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_update_floors_timestamp BEFORE UPDATE ON floors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_update_rooms_timestamp BEFORE UPDATE ON rooms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_update_users_timestamp BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_update_devices_timestamp BEFORE UPDATE ON devices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_update_sensing_templates_timestamp BEFORE UPDATE ON sensing_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_update_alert_templates_timestamp BEFORE UPDATE ON alert_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_update_alert_configurations_timestamp BEFORE UPDATE ON alert_configurations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_update_alerts_timestamp BEFORE UPDATE ON alerts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
