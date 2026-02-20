from neo4j import GraphDatabase


URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")


def run_query(session, query: str) -> None:
    session.run(query).consume()


def seed_organizations(session) -> None:
    run_query(
        session,
        """
        MERGE (vps:Organization {name: 'Vancouver Public Schools'})
        SET vps.type = 'School District',
            vps.ubi = '601-223-961',
            vps.enrollment_2024 = 22500
        """,
    )

    run_query(
        session,
        """
        MERGE (hr:Organization {name: 'VPS Human Resources'})
        SET hr.type = 'Department'
        """,
    )

    run_query(
        session,
        """
        MERGE (finance:Organization {name: 'VPS Finance & Operations'})
        SET finance.type = 'Department'
        """,
    )

    run_query(
        session,
        """
        MERGE (sped:Organization {name: 'VPS Special Education'})
        SET sped.type = 'Department'
        """,
    )

    run_query(
        session,
        """
        MATCH (dept:Organization)
        WHERE dept.type = 'Department'
        MATCH (vps:Organization {name: 'Vancouver Public Schools'})
        MERGE (dept)-[:PART_OF]->(vps)
        """,
    )

    run_query(
        session,
        """
        MERGE (maxim_parent:Organization {name: 'Maxim Healthcare Services'})
        SET maxim_parent.type = 'Parent Company',
            maxim_parent.hq = 'Columbia, MD',
            maxim_parent.notes = '$150M Medicaid fraud settlement (2011). DPA and CIA imposed.'
        """,
    )


def seed_people(session) -> None:
    run_query(
        session,
        """
        MERGE (supt:Person {name: 'Jeff Snell'})
        SET supt.role = 'Superintendent',
            supt.start_date = date('2020-07-01')
        """,
    )

    for name, position in [
        ("Tracie Brennan", "President"),
        ("Kyle Sproul", "Vice President"),
        ("Mark Stoker", None),
        ("Krysta Shendruck", None),
        ("Liz Darling", None),
    ]:
        if position:
            run_query(
                session,
                f"""
                MERGE (b:Person {{name: '{name}'}})
                SET b.role = 'Board Member',
                    b.position = '{position}'
                """,
            )
        else:
            run_query(
                session,
                f"""
                MERGE (b:Person {{name: '{name}'}})
                SET b.role = 'Board Member'
                """,
            )

    run_query(
        session,
        """
        MATCH (supt:Person {name: 'Jeff Snell'}), (vps:Organization {name: 'Vancouver Public Schools'})
        MERGE (supt)-[:EMPLOYED_BY {position: 'Superintendent'}]->(vps)
        """,
    )

    run_query(
        session,
        """
        MATCH (b:Person), (vps:Organization {name: 'Vancouver Public Schools'})
        WHERE b.role = 'Board Member'
        MERGE (b)-[:GOVERNS]->(vps)
        """,
    )


def seed_fiscal_years(session) -> None:
    run_query(
        session,
        """
        UNWIND [
          {label: '2019-20', start: date('2019-09-01'), end: date('2020-08-31')},
          {label: '2020-21', start: date('2020-09-01'), end: date('2021-08-31')},
          {label: '2021-22', start: date('2021-09-01'), end: date('2022-08-31')},
          {label: '2022-23', start: date('2022-09-01'), end: date('2023-08-31')},
          {label: '2023-24', start: date('2023-09-01'), end: date('2024-08-31')},
          {label: '2024-25', start: date('2024-09-01'), end: date('2025-08-31')},
          {label: '2025-26', start: date('2025-09-01'), end: date('2026-08-31')}
        ] AS fy
        MERGE (f:FiscalYear {label: fy.label})
        SET f.start_date = fy.start,
            f.end_date = fy.end
        """,
    )

    run_query(
        session,
        """
        MATCH (vps:Organization {name: 'Vancouver Public Schools'}), (fy:FiscalYear)
        MERGE (vps)-[:HAS_BUDGET]->(fy)
        """,
    )


def seed_budget_objects(session) -> None:
    run_query(
        session,
        """
        UNWIND [
          {code: 1, name: 'Certificated Salaries', desc: 'Teacher and certificated staff salaries'},
          {code: 2, name: 'Classified Salaries', desc: 'Support staff and classified employee salaries'},
          {code: 3, name: 'Employee Benefits', desc: 'Benefits and payroll taxes'},
          {code: 4, name: 'Supplies', desc: 'Supplies, instructional resources, noncapitalized items'},
          {code: 5, name: 'Purchased Services', desc: 'Contracted services from external vendors (Object 7)'},
          {code: 6, name: 'Travel', desc: 'Travel and conference expenses'},
          {code: 7, name: 'Capital Outlay', desc: 'Equipment and capital purchases'},
          {code: 8, name: 'Other', desc: 'Miscellaneous expenditures'},
          {code: 9, name: 'Transfers', desc: 'Inter-fund transfers'}
        ] AS bo
        MERGE (b:BudgetObject {object_code: bo.code})
        SET b.name = bo.name,
            b.description = bo.desc
        """,
    )


def main() -> None:
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        seed_organizations(session)
        seed_people(session)
        seed_fiscal_years(session)
        seed_budget_objects(session)

        node_counts = session.run(
            "MATCH (n) RETURN labels(n) AS labels, count(n) AS c ORDER BY c DESC"
        ).data()
        dept_links = session.run(
            "MATCH (:Organization {name:'Vancouver Public Schools'})<-[:PART_OF]-(:Organization {type:'Department'}) RETURN count(*) AS c"
        ).single()["c"]
        fy_count = session.run("MATCH (:FiscalYear) RETURN count(*) AS c").single()["c"]
        people_links = session.run(
            "MATCH (:Person)-[r:EMPLOYED_BY|GOVERNS]->(:Organization {name:'Vancouver Public Schools'}) RETURN count(r) AS c"
        ).single()["c"]

        print("PHASE3_OK")
        print("NODE_COUNTS", node_counts)
        print(f"DEPARTMENTS_LINKED={dept_links} FY_COUNT={fy_count} PEOPLE_LINKS={people_links}")

    driver.close()


if __name__ == "__main__":
    main()
