from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def run_query(session, title, query):
    print(f"\\n{'='*60}")
    print(f"QUERY: {title}")
    print(f"{'-'*60}")
    result = session.run(query).data()
    for row in result:
        print(row)
    print(f"{'='*60}\\n")

def verify_investigative_queries():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        
        # 1. Total payments to target vendors by fiscal year
        q1 = """
        MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:IN_FISCAL_YEAR]->(fy:FiscalYear)
        WHERE v.normalized_name IN ["Amergis/Maxim", "Soliant Health", "Pioneer Healthcare"]
        RETURN v.normalized_name, fy.label, sum(p.amount) as total, count(p) as payments
        ORDER BY v.normalized_name, fy.label;
        """
        run_query(session, "1. Spending Trajectory by Target Vendor", q1)

        # 2. Rebrand Handoff (Maxim -> Amergis)
        q2 = """
        MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:IN_FISCAL_YEAR]->(fy:FiscalYear)
        WHERE v.normalized_name = "Amergis/Maxim"
        RETURN v.name as actual_payee, fy.label, count(p) as payments, sum(p.amount) as total
        ORDER BY fy.label, v.name;
        """
        run_query(session, "2. Maxim -> Amergis Rebrand Handoff Evidence", q2)

        # 3. Object 7 (Purchased Services) Budget tracking
        q3 = """
        MATCH (fy:FiscalYear)-[s:SPENT]->(bo:BudgetObject)
        WITH fy, sum(s.amount) as total_budget,
             sum(CASE WHEN bo.name = "Purchased Services" THEN s.amount ELSE 0 END) as obj7
        RETURN fy.label, obj7, total_budget, round(obj7/total_budget * 100, 2) as pct
        ORDER BY fy.label;
        """
        run_query(session, "3. Purchased Services Budget Trajectory", q3)

        # 4. Superintendent Salary vs Contractor Spend
        q4 = """
        MATCH (e:Employee {name: 'JEFFREY SNELL'})-[:EMPLOYED_IN]->(fy:FiscalYear)
        OPTIONAL MATCH (fy)<-[s:SPENT_IN_YEAR]-(v:Vendor {normalized_name: 'Amergis/Maxim'})
        RETURN fy.label, e.salary as supt_salary, s.total_amount as amergis_total
        ORDER BY fy.label;
        """
        run_query(session, "4. Superintendent Salary vs Amergis/Maxim Total", q4)
        
        # 5. Governance connection (Consent agenda rubber stamping)
        q5 = """
        MATCH (v:Vendor {normalized_name: 'Amergis/Maxim'})-[:PARTY_TO]->(c:Contract)<-[:AUTHORIZES]-(a:AgendaItem)<-[:HAS_ITEM]-(m:BoardMeeting)
        RETURN m.date, a.section, a.vote_result, c.description
        ORDER BY m.date DESC LIMIT 5;
        """
        run_query(session, "5. Recent Amergis/Maxim Board Approvals (Governance Path)", q5)

    driver.close()

if __name__ == "__main__":
    verify_investigative_queries()
