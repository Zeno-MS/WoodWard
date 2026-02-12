// Auto-generated Budget Load Script
// Source: woodward.db
MERGE (fy:FiscalYear {label: '2022-2023'});
MATCH (vps:Organization {name: 'Vancouver Public Schools'})
MERGE (vps)-[:HAS_BUDGET]->(fy);
MERGE (fy:FiscalYear {label: '2023-2024'});
MATCH (vps:Organization {name: 'Vancouver Public Schools'})
MERGE (vps)-[:HAS_BUDGET]->(fy);
MERGE (fy:FiscalYear {label: '2024-2025'});
MATCH (vps:Organization {name: 'Vancouver Public Schools'})
MERGE (vps)-[:HAS_BUDGET]->(fy);
MERGE (bo:BudgetObject {name: 'Certificated Salaries'}) SET bo.description = 'Teacher and certificated staff salaries';
MERGE (bo:BudgetObject {name: 'Classified Salaries'}) SET bo.description = 'Support staff and classified employee salaries';
MERGE (bo:BudgetObject {name: 'Employee Benefits'}) SET bo.description = 'Benefits and payroll taxes';
MERGE (bo:BudgetObject {name: 'Supplies'}) SET bo.description = 'Supplies, instructional resources, noncapitalized items';
MERGE (bo:BudgetObject {name: 'Purchased Services'}) SET bo.description = 'Contracted services from external vendors';
MERGE (bo:BudgetObject {name: 'Travel'}) SET bo.description = 'Travel and conference expenses';
MERGE (bo:BudgetObject {name: 'Capital Outlay'}) SET bo.description = 'Equipment and capital purchases';
MERGE (bo:BudgetObject {name: 'Other'}) SET bo.description = 'Miscellaneous expenditures';
MERGE (bo:BudgetObject {name: 'Transfers'}) SET bo.description = 'Inter-fund transfers';

MATCH (fy:FiscalYear {label: '2023-2024'})
MATCH (bo:BudgetObject {name: 'Certificated Salaries'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 187285859.0,
r.formatted = '$187,285,859',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2024-2025'})
MATCH (bo:BudgetObject {name: 'Certificated Salaries'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 184673465.0,
r.formatted = '$184,673,465',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2023-2024'})
MATCH (bo:BudgetObject {name: 'Classified Salaries'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 76942910.0,
r.formatted = '$76,942,910',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2024-2025'})
MATCH (bo:BudgetObject {name: 'Classified Salaries'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 79477577.0,
r.formatted = '$79,477,577',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2023-2024'})
MATCH (bo:BudgetObject {name: 'Employee Benefits'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 91997352.0,
r.formatted = '$91,997,352',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2024-2025'})
MATCH (bo:BudgetObject {name: 'Employee Benefits'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 93573843.0,
r.formatted = '$93,573,843',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2023-2024'})
MATCH (bo:BudgetObject {name: 'Supplies'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 16082803.0,
r.formatted = '$16,082,803',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2023-2024'})
MATCH (bo:BudgetObject {name: 'Purchased Services'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 43420672.0,
r.formatted = '$43,420,672',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2024-2025'})
MATCH (bo:BudgetObject {name: 'Purchased Services'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 47331056.0,
r.formatted = '$47,331,056',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2023-2024'})
MATCH (bo:BudgetObject {name: 'Travel'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 721633.0,
r.formatted = '$721,633',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2024-2025'})
MATCH (bo:BudgetObject {name: 'Travel'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 263650.0,
r.formatted = '$263,650',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2023-2024'})
MATCH (bo:BudgetObject {name: 'Capital Outlay'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 1246940.0,
r.formatted = '$1,246,940',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2024-2025'})
MATCH (bo:BudgetObject {name: 'Capital Outlay'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 133500.0,
r.formatted = '$133,500',
r.source = 'VPS_2025-26_F-195.pdf';


MATCH (fy:FiscalYear {label: '2022-2023'})
MATCH (bo:BudgetObject {name: 'Certificated Salaries'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 177388844.0,
r.formatted = '$177,388,844',
r.source = 'VPS_2024-25_F-195.pdf';


MATCH (fy:FiscalYear {label: '2022-2023'})
MATCH (bo:BudgetObject {name: 'Classified Salaries'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 70109045.0,
r.formatted = '$70,109,045',
r.source = 'VPS_2024-25_F-195.pdf';


MATCH (fy:FiscalYear {label: '2022-2023'})
MATCH (bo:BudgetObject {name: 'Employee Benefits'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 93082611.0,
r.formatted = '$93,082,611',
r.source = 'VPS_2024-25_F-195.pdf';


MATCH (fy:FiscalYear {label: '2022-2023'})
MATCH (bo:BudgetObject {name: 'Supplies'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 14821609.0,
r.formatted = '$14,821,609',
r.source = 'VPS_2024-25_F-195.pdf';


MATCH (fy:FiscalYear {label: '2022-2023'})
MATCH (bo:BudgetObject {name: 'Purchased Services'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 42056089.0,
r.formatted = '$42,056,089',
r.source = 'VPS_2024-25_F-195.pdf';


MATCH (fy:FiscalYear {label: '2022-2023'})
MATCH (bo:BudgetObject {name: 'Travel'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 933263.0,
r.formatted = '$933,263',
r.source = 'VPS_2024-25_F-195.pdf';


MATCH (fy:FiscalYear {label: '2022-2023'})
MATCH (bo:BudgetObject {name: 'Capital Outlay'})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = 4586906.0,
r.formatted = '$4,586,906',
r.source = 'VPS_2024-25_F-195.pdf';

