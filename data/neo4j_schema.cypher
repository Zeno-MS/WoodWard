// WoodWard Neo4j Schema
// SEGREGATED from CaseLawDB - runs on port 7688

// ============================================
// CONSTRAINTS (ensure data integrity)
// ============================================

CREATE CONSTRAINT person_name IF NOT EXISTS
FOR (p:Person) REQUIRE p.name IS UNIQUE;

CREATE CONSTRAINT organization_name IF NOT EXISTS
FOR (o:Organization) REQUIRE o.name IS UNIQUE;

CREATE CONSTRAINT contract_number IF NOT EXISTS
FOR (c:Contract) REQUIRE c.contract_number IS UNIQUE;

CREATE CONSTRAINT document_filename IF NOT EXISTS
FOR (d:Document) REQUIRE d.filename IS UNIQUE;

// ============================================
// INDEXES (performance)
// ============================================

CREATE INDEX person_role IF NOT EXISTS
FOR (p:Person) ON (p.role);

CREATE INDEX organization_type IF NOT EXISTS
FOR (o:Organization) ON (o.type);

CREATE INDEX contract_value IF NOT EXISTS
FOR (c:Contract) ON (c.total_value);

CREATE INDEX meeting_date IF NOT EXISTS
FOR (m:Meeting) ON (m.date);

// ============================================
// INITIAL DATA: VPS Leadership
// ============================================

// School District
MERGE (vps:Organization {name: "Vancouver Public Schools"})
SET vps.type = "School District",
    vps.ubi = "601-223-961",
    vps.enrollment_2024 = 22500;

// Superintendent
MERGE (supt:Person {name: "Jeff Snell"})
SET supt.role = "Superintendent",
    supt.start_date = date("2020-07-01");

// Board Members (2024-2025)
MERGE (b1:Person {name: "Tracie Brennan"})
SET b1.role = "Board Member", b1.position = "President";

MERGE (b2:Person {name: "Kyle Sproul"})
SET b2.role = "Board Member", b2.position = "Vice President";

MERGE (b3:Person {name: "Mark Stoker"})
SET b3.role = "Board Member";

MERGE (b4:Person {name: "Krysta Shendruck"})
SET b4.role = "Board Member";

MERGE (b5:Person {name: "Liz Darling"})
SET b5.role = "Board Member";

// Relationships
MATCH (supt:Person {name: "Jeff Snell"}), (vps:Organization {name: "Vancouver Public Schools"})
MERGE (supt)-[:EMPLOYED_BY {position: "Superintendent"}]->(vps);

MATCH (b:Person), (vps:Organization {name: "Vancouver Public Schools"})
WHERE b.role = "Board Member"
MERGE (b)-[:GOVERNS]->(vps);

// ============================================
// KEY DEPARTMENTS & DIRECTORS
// ============================================

MERGE (hr:Organization {name: "VPS Human Resources"})
SET hr.type = "Department";

MERGE (finance:Organization {name: "VPS Finance & Operations"})
SET finance.type = "Department";

MERGE (sped:Organization {name: "VPS Special Education"})
SET sped.type = "Department";

// Link departments to district
MATCH (dept:Organization), (vps:Organization {name: "Vancouver Public Schools"})
WHERE dept.type = "Department"
MERGE (dept)-[:PART_OF]->(vps);
