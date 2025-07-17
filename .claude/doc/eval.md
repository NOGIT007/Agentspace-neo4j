Of course. I have merged the evaluation script into your project. Here are the updated files and the new file structure:

### `eval_project/README.md`

````markdown
# Neo4j Database Agent Evaluation

This project contains a set of evaluation files to test the functionality and robustness of the Neo4j database agent. The evaluation is focused on three primary use cases:

1.  **Callback Resilience Testing**: The `callback_tests.py` file provides a plan and code examples to test the resilience of the system's callbacks under various conditions, including error states and unexpected inputs.

2.  **Database Query Testing**: The `questions.py` file contains over 100 questions designed to test the database query capabilities. These questions cover a wide range of scenarios based on the provided Neo4j database schema, from simple data retrieval to complex aggregations and graph analysis.

3.  **Comprehensive Evaluation Runner**: The `run_evaluation.py` script executes a suite of 50 pre-defined Cypher queries against the Neo4j database and generates a detailed performance and data quality report.

## Usage

-   **`questions.py`**: Use the questions in this file to test the agent's ability to understand natural language queries and translate them into accurate Cypher queries. The questions are categorized by the type of query to allow for targeted testing.

-   **`callback_tests.py`**: This file contains a plan to test the callbacks. The goal is to identify potential weaknesses and ensure the system can handle unexpected situations gracefully.

-   **`run_evaluation.py`**: This script provides a comprehensive evaluation of the database and agent's performance. To run it, you will need to have Python installed with the `neo4j` and `pandas` libraries. You can install them with `pip install neo4j pandas`. Then, from your terminal, run the script with the following command:

    ```bash
    python eval_project/run_evaluation.py
    ```
````

### `eval_project/run_evaluation.py`

```python
#!/usr/bin/env python3
"""
Neo4j ERP Database Evaluation Test Runner
Executes all 50 evaluation queries and generates baseline results
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from neo4j import GraphDatabase
    import pandas as pd
except ImportError as e:
    print(f"Missing required packages. Install with:")
    print(f"pip install neo4j pandas")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('neo4j_evaluation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Structure for storing query execution results"""
    query_id: str
    category: str
    difficulty: str
    question: str
    cypher_query: str
    execution_time_ms: float
    record_count: int
    success: bool
    error_message: Optional[str]
    result_data: List[Dict[str, Any]]
    result_summary: Dict[str, Any]
    business_context: str

@dataclass
class EvaluationReport:
    """Complete evaluation report structure"""
    test_run_id: str
    timestamp: str
    database_info: Dict[str, Any]
    total_queries: int
    successful_queries: int
    failed_queries: int
    total_execution_time_ms: float
    query_results: List[QueryResult]
    performance_summary: Dict[str, Any]
    data_quality_metrics: Dict[str, Any]

class Neo4jEvaluationRunner:
    """Main class for running Neo4j evaluation queries"""
    
    def __init__(self, uri: str, username: str, password: str):
        """Initialize Neo4j connection"""
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self.evaluation_queries = self._load_evaluation_queries()
        
    def connect(self) -> bool:
        """Establish connection to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("Successfully connected to Neo4j database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def _load_evaluation_queries(self) -> List[Dict[str, Any]]:
        """Load all 50 evaluation queries with metadata"""
        return [
            # CATEGORY 1: DATA RETRIEVAL & QUERIES (Questions 1-15)
            {
                "id": "eval_001",
                "category": "Data Retrieval",
                "difficulty": "Easy",
                "question": "Retrieve all active customers with their total number of invoices",
                "cypher": """
                MATCH (c:Customer)-[:HAS_INVOICE]->(i:Invoice)
                WHERE c.status = 'ACTIVE' OR c.status IS NULL
                RETURN c.name, c.customerID, count(i) as total_invoices
                ORDER BY total_invoices DESC
                """,
                "business_context": "Customer portfolio analysis"
            },
            {
                "id": "eval_002",
                "category": "Data Retrieval",
                "difficulty": "Easy",
                "question": "Find all invoices issued in 2024 with their status",
                "cypher": """
                MATCH (i:Invoice)
                WHERE i.issue_date >= date('2024-01-01') AND i.issue_date <= date('2024-12-31')
                RETURN i.invoiceNumber, i.issue_date, i.status, i.total_amount
                ORDER BY i.issue_date DESC
                """,
                "business_context": "Annual financial review"
            },
            {
                "id": "eval_003",
                "category": "Data Retrieval",
                "difficulty": "Medium",
                "question": "List all subscription items for a specific customer including product details",
                "cypher": """
                MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s:Subscription)
                MATCH (s)-[:CONTAINS_ITEM]->(si:SubscriptionItem)-[:FOR_PRODUCT]->(p:Product)
                RETURN c.name, s.subscriptionID, si.item_description, 
                        p.product_name, si.quantity, si.unit_price, si.total_price
                ORDER BY si.line_number
                LIMIT 100
                """,
                "business_context": "Customer account review"
            },
            {
                "id": "eval_004",
                "category": "Data Retrieval",
                "difficulty": "Hard",
                "question": "Find customers who have both active subscriptions and unresolved support tickets",
                "cypher": """
                MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s:Subscription)
                WHERE s.status = 'ACTIVE'
                MATCH (c)-[:RAISED_CASE]->(case:Case)
                WHERE case.status IN ['OPEN', 'IN_PROGRESS']
                RETURN DISTINCT c.name, c.customerID, 
                        count(DISTINCT s) as active_subscriptions,
                        count(DISTINCT case) as open_tickets
                ORDER BY open_tickets DESC, active_subscriptions DESC
                """,
                "business_context": "Customer success management"
            },
            {
                "id": "eval_005",
                "category": "Data Retrieval",
                "difficulty": "Medium",
                "question": "Retrieve all credit notes with their original invoice details",
                "cypher": """
                MATCH (cn:Invoice {invoice_document_type: 'Credit Note'})-[:CREDITS_INVOICE]->(original:Invoice)
                RETURN cn.invoiceNumber as credit_note_number,
                        cn.total_amount as credit_amount,
                        cn.issue_date as credit_date,
                        original.invoiceNumber as original_invoice,
                        original.total_amount as original_amount,
                        original.issue_date as original_date
                ORDER BY cn.issue_date DESC
                """,
                "business_context": "Financial reconciliation"
            },
            {
                "id": "eval_006",
                "category": "Data Retrieval",
                "difficulty": "Medium",
                "question": "Find the top 10 customers by total invoice value in the last 12 months",
                "cypher": """
                MATCH (c:Customer)-[:HAS_INVOICE]->(i:Invoice)
                WHERE i.issue_date >= date() - duration({months: 12})
                  AND i.invoice_document_type = 'Invoice'
                WITH c, sum(i.total_amount) as total_revenue
                RETURN c.name, c.customerID, total_revenue
                ORDER BY total_revenue DESC
                LIMIT 10
                """,
                "business_context": "Key account identification"
            },
            {
                "id": "eval_007",
                "category": "Data Retrieval",
                "difficulty": "Hard",
                "question": "Calculate average resolution time for support tickets by category",
                "cypher": """
                MATCH (case:Case)-[:BELONGS_TO_CATEGORY]->(tc:TicketCategory)
                WHERE case.resolution_date IS NOT NULL AND case.created_date IS NOT NULL
                WITH tc.category_name as category, 
                    duration.between(case.created_date, case.resolution_date).days as resolution_days
                RETURN category, 
                        avg(resolution_days) as avg_resolution_days,
                        count(*) as total_resolved_cases
                ORDER BY avg_resolution_days DESC
                """,
                "business_context": "SLA monitoring"
            },
            {
                "id": "eval_008",
                "category": "Data Retrieval",
                "difficulty": "Easy",
                "question": "Find invoices without corresponding invoice lines",
                "cypher": """
                MATCH (i:Invoice)
                WHERE NOT EXISTS((i)-[:CONTAINS_LINE]->(:InvoiceLine))
                RETURN i.invoiceID, i.invoiceNumber, i.invoice_document_type, i.total_amount
                ORDER BY i.issue_date DESC
                """,
                "business_context": "Data quality audit"
            },
            {
                "id": "eval_009",
                "category": "Data Retrieval",
                "difficulty": "Medium",
                "question": "Identify customers with subscriptions but no recent invoices (last 3 months)",
                "cypher": """
                MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s:Subscription)
                WHERE s.status = 'ACTIVE'
                OPTIONAL MATCH (c)-[:HAS_INVOICE]->(i:Invoice)
                WHERE i.issue_date >= date() - duration({months: 3})
                WITH c, s, count(i) as recent_invoices
                WHERE recent_invoices = 0
                RETURN c.name, c.customerID, s.subscriptionID, s.start_date
                ORDER BY s.start_date
                """,
                "business_context": "Revenue assurance"
            },
            {
                "id": "eval_010",
                "category": "Data Retrieval",
                "difficulty": "Hard",
                "question": "Find subscription changes that resulted in MRR increase > 20%",
                "cypher": """
                MATCH (s:Subscription)-[:HAS_CHANGE]->(sc:SubscriptionChange)
                WHERE sc.mrr_impact > 0 AND s.mrr > 0
                WITH s, sc, (sc.mrr_impact / s.mrr * 100) as mrr_increase_percent
                WHERE mrr_increase_percent > 20
                RETURN s.subscriptionID, sc.change_type, sc.change_reason,
                        s.mrr as current_mrr, sc.mrr_impact, mrr_increase_percent
                ORDER BY mrr_increase_percent DESC
                """,
                "business_context": "Revenue growth analysis"
            },
            {
                "id": "eval_011",
                "category": "Data Retrieval",
                "difficulty": "Medium",
                "question": "Calculate monthly invoice volumes for the current year",
                "cypher": """
                MATCH (i:Invoice)
                WHERE i.issue_date.year = date().year
                WITH i.issue_date.month as month, i.invoice_document_type as doc_type, count(*) as volume
                RETURN month, 
                        sum(CASE WHEN doc_type = 'Invoice' THEN volume ELSE 0 END) as invoices,
                        sum(CASE WHEN doc_type = 'Credit Note' THEN volume ELSE 0 END) as credit_notes,
                        sum(volume) as total_documents
                ORDER BY month
                """,
                "business_context": "Billing operations monitoring"
            },
            {
                "id": "eval_012",
                "category": "Data Retrieval",
                "difficulty": "Hard",
                "question": "Track payment collection efficiency by month",
                "cypher": """
                MATCH (i:Invoice {invoice_document_type: 'Invoice'})<-[:PAYS_INVOICE]-(p:Payment)
                WHERE i.issue_date.year = 2024
                WITH i.issue_date.month as month,
                    i.total_amount as invoice_amount,
                    p.amount as payment_amount,
                    duration.between(i.issue_date, p.paymentDate).days as days_to_payment
                RETURN month,
                        count(*) as paid_invoices,
                        sum(invoice_amount) as invoiced_amount,
                        sum(payment_amount) as collected_amount,
                        avg(days_to_payment) as avg_collection_days
                ORDER BY month
                """,
                "business_context": "Cash flow management"
            },
            {
                "id": "eval_013",
                "category": "Data Retrieval",
                "difficulty": "Medium",
                "question": "Find products that have never been included in any subscription",
                "cypher": """
                MATCH (p:Product)
                WHERE NOT EXISTS((p)<-[:FOR_PRODUCT]-(:SubscriptionItem))
                RETURN p.productID, p.product_name, p.status, p.created_date
                ORDER BY p.created_date DESC
                """,
                "business_context": "Product portfolio optimization"
            },
            {
                "id": "eval_014",
                "category": "Data Retrieval",
                "difficulty": "Hard",
                "question": "Identify customer churn patterns by analyzing cancelled subscriptions",
                "cypher": """
                MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s:Subscription)
                WHERE s.status = 'CANCELLED' AND s.end_date IS NOT NULL
                WITH c, s, duration.between(s.start_date, s.end_date).days as subscription_lifetime
                RETURN c.customer_segment,
                        count(*) as churned_customers,
                        avg(subscription_lifetime) as avg_lifetime_days,
                        avg(s.mrr) as avg_monthly_revenue
                ORDER BY churned_customers DESC
                """,
                "business_context": "Customer retention strategy"
            },
            {
                "id": "eval_015",
                "category": "Data Retrieval",
                "difficulty": "Medium",
                "question": "List all support tickets that resulted in credit notes with financial impact",
                "cypher": """
                MATCH (ticket:Case)-[:RESULTED_IN_CREDIT_NOTE]->(cn:Invoice)
                MATCH (cn)-[:CREDITS_INVOICE]->(original:Invoice)
                MATCH (customer:Customer)-[:RAISED_CASE]->(ticket)
                RETURN customer.name, ticket.subject, ticket.created_date,
                        ticket.case_category, original.total_amount as original_amount,
                        cn.total_amount as credit_amount,
                        abs(cn.total_amount / original.total_amount * 100) as credit_percentage
                ORDER BY abs(cn.total_amount) DESC
                """,
                "business_context": "Service quality impact analysis"
            },
            
            # CATEGORY 2: BUSINESS LOGIC & RELATIONSHIPS (Questions 16-25)
            {
                "id": "eval_016",
                "category": "Business Logic",
                "difficulty": "Medium",
                "question": "Validate that all credit notes have negative amounts and reference original invoices",
                "cypher": """
                MATCH (cn:Invoice {invoice_document_type: 'Credit Note'})
                OPTIONAL MATCH (cn)-[:CREDITS_INVOICE]->(original:Invoice)
                RETURN cn.invoiceNumber,
                        cn.total_amount,
                        cn.total_amount < 0 as has_negative_amount,
                        original.invoiceNumber as references_original,
                        EXISTS((cn)-[:CREDITS_INVOICE]->()) as has_reference
                ORDER BY cn.issue_date DESC
                """,
                "business_context": "Financial data integrity"
            },
            {
                "id": "eval_017",
                "category": "Business Logic",
                "difficulty": "Hard",
                "question": "Verify subscription billing consistency - ensure MRR matches invoice amounts",
                "cypher": """
                MATCH (s:Subscription)-[:FOR_SUBSCRIPTION]-(i:Invoice {invoice_document_type: 'Invoice'})
                WHERE s.mrr IS NOT NULL AND i.total_amount IS NOT NULL
                  AND i.issue_date >= date() - duration({months: 6})
                WITH s, avg(i.total_amount) as avg_monthly_invoice
                RETURN s.subscriptionID, s.mrr, avg_monthly_invoice,
                        abs(s.mrr - avg_monthly_invoice) as variance,
                        abs(s.mrr - avg_monthly_invoice) / s.mrr * 100 as variance_percent
                ORDER BY variance_percent DESC
                LIMIT 20
                """,
                "business_context": "Revenue accuracy validation"
            },
            {
                "id": "eval_018",
                "category": "Business Logic",
                "difficulty": "Medium",
                "question": "Check payment completeness - find invoices without corresponding payments",
                "cypher": """
                MATCH (i:Invoice {invoice_document_type: 'Invoice'})
                WHERE i.status = 'PAID'
                OPTIONAL MATCH (i)<-[:PAYS_INVOICE]-(p:Payment)
                WITH i, sum(p.amount) as total_payments
                WHERE total_payments IS NULL OR total_payments < i.total_amount
                RETURN i.invoiceNumber, i.total_amount, total_payments,
                        i.total_amount - coalesce(total_payments, 0) as outstanding_amount
                ORDER BY outstanding_amount DESC
                """,
                "business_context": "Accounts receivable accuracy"
            },
            {
                "id": "eval_019",
                "category": "Business Logic",
                "difficulty": "Hard",
                "question": "Validate subscription lifecycle - check for overlapping active subscriptions per customer",
                "cypher": """
                MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s1:Subscription),
                        (c)-[:HAS_SUBSCRIPTION]->(s2:Subscription)
                WHERE s1.subscriptionID <> s2.subscriptionID
                  AND s1.status = 'ACTIVE' AND s2.status = 'ACTIVE'
                  AND s1.start_date <= s2.end_date AND s2.start_date <= s1.end_date
                RETURN c.name, c.customerID,
                        s1.subscriptionID as subscription1,
                        s2.subscriptionID as subscription2,
                        s1.start_date as start1, s1.end_date as end1,
                        s2.start_date as start2, s2.end_date as end2
                ORDER BY c.name
                """,
                "business_context": "Subscription management integrity"
            },
            {
                "id": "eval_020",
                "category": "Business Logic",
                "difficulty": "Medium",
                "question": "Ensure all invoice lines sum to invoice totals",
                "cypher": """
                MATCH (i:Invoice)-[:CONTAINS_LINE]->(il:InvoiceLine)
                WITH i, sum(il.line_total) as calculated_total
                WHERE abs(i.total_amount - calculated_total) > 0.01
                RETURN i.invoiceNumber, i.total_amount, calculated_total,
                        i.total_amount - calculated_total as variance
                ORDER BY abs(variance) DESC
                """,
                "business_context": "Financial accuracy audit"
            },
            {
                "id": "eval_021",
                "category": "Business Logic",
                "difficulty": "Hard",
                "question": "Track complete customer journey from subscription to support to billing",
                "cypher": """
                MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s:Subscription)
                OPTIONAL MATCH (c)-[:RAISED_CASE]->(case:Case)
                OPTIONAL MATCH (c)-[:HAS_INVOICE]->(i:Invoice)
                WHERE s.start_date >= date('2024-01-01')
                RETURN c.name, s.start_date, s.status,
                        count(DISTINCT case) as support_tickets,
                        count(DISTINCT i) as total_invoices,
                        sum(CASE WHEN i.invoice_document_type = 'Credit Note' THEN 1 ELSE 0 END) as credit_notes
                ORDER BY s.start_date DESC
                LIMIT 50
                """,
                "business_context": "Customer experience tracking"
            },
            {
                "id": "eval_022",
                "category": "Business Logic",
                "difficulty": "Medium",
                "question": "Validate SLA compliance for support tickets by category",
                "cypher": """
                MATCH (case:Case)-[:BELONGS_TO_CATEGORY]->(tc:TicketCategory)
                WHERE case.resolution_date IS NOT NULL
                WITH case, tc, 
                    duration.between(case.created_date, case.resolution_date).hours as resolution_hours
                RETURN tc.category_name, tc.sla_hours,
                        count(*) as total_cases,
                        count(CASE WHEN resolution_hours <= tc.sla_hours THEN 1 END) as within_sla,
                        count(CASE WHEN resolution_hours > tc.sla_hours THEN 1 END) as sla_breached,
                        avg(resolution_hours) as avg_resolution_hours
                ORDER BY tc.category_name
                """,
                "business_context": "Service level monitoring"
            },
            {
                "id": "eval_023",
                "category": "Business Logic",
                "difficulty": "Hard",
                "question": "Detect potential revenue leakage - active subscriptions without recent invoices",
                "cypher": """
                MATCH (s:Subscription)
                WHERE s.status = 'ACTIVE' AND s.start_date < date() - duration({months: 1})
                OPTIONAL MATCH (s)<-[:FOR_SUBSCRIPTION]-(i:Invoice)
                WHERE i.issue_date >= date() - duration({months: 2})
                WITH s, count(i) as recent_invoices
                WHERE recent_invoices = 0
                MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s)
                RETURN c.name, s.subscriptionID, s.start_date, s.mrr,
                        s.mrr * 2 as potential_lost_revenue
                ORDER BY potential_lost_revenue DESC
                """,
                "business_context": "Revenue assurance monitoring"
            },
            {
                "id": "eval_024",
                "category": "Business Logic",
                "difficulty": "Medium",
                "question": "Verify customer contact information completeness",
                "cypher": """
                MATCH (c:Customer)
                OPTIONAL MATCH (c)-[:HAS_CONTACT]->(contact:Contact {is_primary: true})
                RETURN c.customerID, c.name,
                        c.email IS NOT NULL as has_customer_email,
                        contact.email IS NOT NULL as has_primary_contact,
                        c.phone IS NOT NULL as has_phone,
                        c.billing_address IS NOT NULL as has_billing_address,
                        CASE 
                            WHEN c.email IS NOT NULL AND contact.email IS NOT NULL 
                                AND c.phone IS NOT NULL AND c.billing_address IS NOT NULL 
                            THEN 'Complete'
                            ELSE 'Incomplete'
                        END as contact_completeness
                ORDER BY contact_completeness, c.name
                LIMIT 100
                """,
                "business_context": "Data quality management"
            },
            {
                "id": "eval_025",
                "category": "Business Logic",
                "difficulty": "Hard",
                "question": "Analyze subscription change patterns and their financial impact",
                "cypher": """
                MATCH (s:Subscription)-[:HAS_CHANGE]->(sc:SubscriptionChange)
                WHERE sc.executed_date IS NOT NULL
                MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s)
                WITH sc.change_type as change_type,
                    sum(sc.mrr_impact) as total_mrr_impact,
                    count(*) as change_count,
                    avg(sc.mrr_impact) as avg_mrr_impact
                RETURN change_type, change_count, total_mrr_impact, avg_mrr_impact,
                        total_mrr_impact * 12 as annual_impact
                ORDER BY total_mrr_impact DESC
                """,
                "business_context": "Revenue change analysis"
            },
            
            # CATEGORY 3: FINANCIAL ANALYSIS (Questions 26-35)
            {
                "id": "eval_026",
                "category": "Financial Analysis",
                "difficulty": "Medium",
                "question": "Calculate current MRR from active subscriptions",
                "cypher": """
                MATCH (s:Subscription)
                WHERE s.status = 'ACTIVE' AND s.mrr IS NOT NULL
                RETURN sum(s.mrr) as total_mrr,
                        count(s) as active_subscriptions,
                        avg(s.mrr) as avg_mrr_per_subscription,
                        sum(s.mrr) * 12 as projected_arr
                """,
                "business_context": "Revenue tracking"
            },
            {
                "id": "eval_027",
                "category": "Financial Analysis",
                "difficulty": "Hard",
                "question": "Calculate customer lifetime value (LTV) based on subscription history",
                "cypher": """
                MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s:Subscription)
                OPTIONAL MATCH (c)-[:HAS_INVOICE]->(i:Invoice {invoice_document_type: 'Invoice'})
                WITH c, 
                    min(s.start_date) as first_subscription,
                    max(coalesce(s.end_date, date())) as last_activity,
                    sum(s.mrr) as total_mrr,
                    sum(i.total_amount) as total_invoiced
                WITH c, first_subscription, last_activity,
                    duration.between(first_subscription, last_activity).months as lifetime_months,
                    total_mrr, total_invoiced
                WHERE lifetime_months > 0
                RETURN c.name, first_subscription, lifetime_months,
                        total_invoiced, total_invoiced / lifetime_months as avg_monthly_revenue,
                        total_invoiced as ltv
                ORDER BY ltv DESC
                LIMIT 20
                """,
                "business_context": "Customer value analysis"
            },
            {
                "id": "eval_028",
                "category": "Financial Analysis",
                "difficulty": "Medium",
                "question": "Analyze credit note impact on monthly revenue",
                "cypher": """
                MATCH (i:Invoice)
                WHERE i.issue_date >= date() - duration({months: 12})
                WITH i.issue_date.year as year, i.issue_date.month as month,
                    sum(CASE WHEN i.invoice_document_type = 'Invoice' THEN i.total_amount ELSE 0 END) as gross_revenue,
                    sum(CASE WHEN i.invoice_document_type = 'Credit Note' THEN abs(i.total_amount) ELSE 0 END) as credit_notes
                RETURN year, month, gross_revenue, credit_notes,
                        gross_revenue - credit_notes as net_revenue,
                        credit_notes / gross_revenue * 100 as credit_note_percentage
                ORDER BY year, month
                """,
                "business_context": "Revenue quality analysis"
            },
            {
                "id": "eval_029",
                "category": "Financial Analysis",
                "difficulty": "Hard",
                "question": "Calculate accounts receivable aging analysis",
                "cypher": """
                MATCH (i:Invoice {invoice_document_type: 'Invoice'})
                WHERE i.status IN ['SENT', 'OVERDUE'] AND i.due_date IS NOT NULL
                OPTIONAL MATCH (i)<-[:PAYS_INVOICE]-(p:Payment)
                WITH i, sum(p.amount) as payments_received,
                    i.total_amount - coalesce(sum(p.amount), 0) as outstanding_amount,
                    duration.between(i.due_date, date()).days as days_overdue
                WHERE outstanding_amount > 0
                WITH CASE 
                        WHEN days_overdue <= 0 THEN 'Current'
                        WHEN days_overdue <= 30 THEN '1-30 days'
                        WHEN days_overdue <= 60 THEN '31-60 days'
                        WHEN days_overdue <= 90 THEN '61-90 days'
                        ELSE '90+ days'
                    END as aging_bucket,
                    outstanding_amount
                RETURN aging_bucket, 
                        count(*) as invoice_count,
                        sum(outstanding_amount) as total_outstanding
                ORDER BY 
                    CASE aging_bucket
                        WHEN 'Current' THEN 1
                        WHEN '1-30 days' THEN 2
                        WHEN '31-60 days' THEN 3
                        WHEN '61-90 days' THEN 4
                        ELSE 5
                    END
                """,
                "business_context": "Collections management"
            },
            {
                "id": "eval_030",
                "category": "Financial Analysis",
                "difficulty": "Medium",
                "question": "Compare actual vs expected revenue based on subscription MRR",
                "cypher": """
                MATCH (s:Subscription {status: 'ACTIVE'})
                WITH sum(s.mrr) as expected_monthly_revenue
                MATCH (i:Invoice {invoice_document_type: 'Invoice'})
                WHERE i.issue_date >= date() - duration({months: 1})
                  AND i.issue_date < date()
                WITH expected_monthly_revenue, sum(i.total_amount) as actual_revenue
                RETURN expected_monthly_revenue, actual_revenue,
                        actual_revenue - expected_monthly_revenue as variance,
                        (actual_revenue - expected_monthly_revenue) / expected_monthly_revenue * 100 as variance_percent
                """,
                "business_context": "Financial planning accuracy"
            },
            {
                "id": "eval_031",
                "category": "Financial Analysis",
                "difficulty": "Hard",
                "question": "Calculate churn impact on revenue - analyze lost MRR from cancelled subscriptions",
                "cypher": """
                MATCH (s:Subscription {status: 'CANCELLED'})
                WHERE s.end_date >= date() - duration({months: 12})
                WITH s.end_date.year as year, s.end_date.month as month,
                    sum(s.mrr) as churned_mrr,
                    count(*) as churned_subscriptions
                MATCH (active:Subscription {status: 'ACTIVE'})
                WITH year, month, churned_mrr, churned_subscriptions,
                    sum(active.mrr) as current_active_mrr
                RETURN year, month, churned_subscriptions, churned_mrr,
                        churned_mrr / (current_active_mrr + churned_mrr) * 100 as churn_rate_percent,
                        churned_mrr * 12 as annual_revenue_impact
                ORDER BY year, month
                """,
                "business_context": "Revenue retention analysis"
            },
            {
                "id": "eval_032",
                "category": "Financial Analysis",
                "difficulty": "Medium",
                "question": "Analyze payment collection patterns and cash flow timing",
                "cypher": """
                MATCH (i:Invoice {invoice_document_type: 'Invoice'})<-[:PAYS_INVOICE]-(p:Payment)
                WHERE i.issue_date >= date() - duration({months: 6})
                WITH duration.between(i.issue_date, p.paymentDate).days as collection_days,
                    p.amount as payment_amount
                WITH CASE 
                        WHEN collection_days <= 7 THEN 'Week 1'
                        WHEN collection_days <= 14 THEN 'Week 2'
                        WHEN collection_days <= 30 THEN 'Month 1'
                        WHEN collection_days <= 60 THEN 'Month 2'
                        ELSE 'Over 60 days'
                    END as collection_period,
                    payment_amount
                RETURN collection_period,
                        count(*) as payment_count,
                        sum(payment_amount) as total_collected,
                        avg(payment_amount) as avg_payment_amount
                ORDER BY 
                    CASE collection_period
                        WHEN 'Week 1' THEN 1
                        WHEN 'Week 2' THEN 2
                        WHEN 'Month 1' THEN 3
                        WHEN 'Month 2' THEN 4
                        ELSE 5
                    END
                """,
                "business_context": "Cash flow optimization"
            },
            {
                "id": "eval_033",
                "category": "Financial Analysis",
                "difficulty": "Hard",
                "question": "Calculate product profitability based on subscription items",
                "cypher": """
                MATCH (p:Product)<-[:FOR_PRODUCT]-(si:SubscriptionItem)
                MATCH (si)<-[:BILLS_FOR]-(il:InvoiceLine)
                WITH p, sum(il.line_total) as revenue, count(DISTINCT si) as subscription_items
                RETURN p.product_name, revenue, subscription_items,
                        revenue / subscription_items as avg_revenue_per_item
                ORDER BY revenue DESC
                """,
                "business_context": "Product portfolio optimization"
            },
            {
                "id": "eval_034",
                "category": "Financial Analysis",
                "difficulty": "Medium",
                "question": "Track invoice payment completion rates by month",
                "cypher": """
                MATCH (i:Invoice {invoice_document_type: 'Invoice'})
                WHERE i.issue_date >= date() - duration({months: 12})
                OPTIONAL MATCH (i)<-[:PAYS_INVOICE]-(p:Payment)
                WITH i.issue_date.year as year, i.issue_date.month as month,
                    i, sum(p.amount) as total_payments
                WITH year, month,
                    count(i) as total_invoices,
                    sum(i.total_amount) as total_invoiced,
                    count(CASE WHEN total_payments >= i.total_amount THEN 1 END) as fully_paid_count,
                    sum(coalesce(total_payments, 0)) as total_collected
                RETURN year, month, total_invoices, fully_paid_count,
                        fully_paid_count * 100.0 / total_invoices as payment_completion_rate,
                        total_collected * 100.0 / total_invoiced as collection_rate
                ORDER BY year, month
                """,
                "business_context": "Collections performance tracking"
            },
            {
                "id": "eval_035",
                "category": "Financial Analysis",
                "difficulty": "Hard",
                "question": "Forecast revenue based on current active subscriptions",
                "cypher": """
                MATCH (s:Subscription {status: 'ACTIVE'})
                WITH sum(s.mrr) as current_mrr, count(s) as active_subscriptions
                MATCH (historical:Subscription)
                WHERE historical.start_date >= date() - duration({months: 12})
                WITH current_mrr, active_subscriptions,
                    count(historical) as new_subscriptions_12m,
                    avg(historical.mrr) as avg_new_mrr
                RETURN current_mrr,
                        current_mrr * 12 as current_arr,
                        new_subscriptions_12m / 12.0 as monthly_new_subscriptions,
                        avg_new_mrr,
                        (current_mrr + (new_subscriptions_12m / 12.0) * avg_new_mrr * 12) * 12 as forecasted_arr_12m
                """,
                "business_context": "Financial planning and budgeting"
            },
            
            # CATEGORY 4: CUSTOMER MANAGEMENT (Questions 36-40)
            {
                "id": "eval_036",
                "category": "Customer Management",
                "difficulty": "Medium",
                "question": "Identify customers at risk based on support ticket volume",
                "cypher": """
                MATCH (c:Customer)
                OPTIONAL MATCH (c)-[:RAISED_CASE]->(case:Case)
                WHERE case.created_date >= date() - duration({months: 3})
                  AND case.status IN ['OPEN', 'IN_PROGRESS']
                WITH c, count(DISTINCT case) as recent_tickets
                WHERE recent_tickets > 1
                MATCH (c)-[:HAS_SUBSCRIPTION]->(s:Subscription {status: 'ACTIVE'})
                RETURN c.name, c.customerID, recent_tickets,
                        sum(s.mrr) as monthly_revenue_at_risk,
                        CASE 
                            WHEN recent_tickets > 3 THEN 'High Risk'
                            WHEN recent_tickets > 2 THEN 'Medium Risk'
                            ELSE 'Low Risk'
                        END as risk_level
                ORDER BY monthly_revenue_at_risk DESC
                """,
                "business_context": "Customer success management"
            },
            {
                "id": "eval_037",
                "category": "Customer Management",
                "difficulty": "Hard",
                "question": "Calculate customer health score based on multiple factors",
                "cypher": """
                MATCH (c:Customer)
                OPTIONAL MATCH (c)-[:HAS_SUBSCRIPTION]->(s:Subscription)
                OPTIONAL MATCH (c)-[:RAISED_CASE]->(case:Case)
                WHERE case.created_date >= date() - duration({months: 6})
                WITH c,
                    count(DISTINCT s) as active_subscriptions,
                    sum(CASE WHEN s.status = 'ACTIVE' THEN s.mrr ELSE 0 END) as current_mrr,
                    count(DISTINCT case) as recent_support_tickets
                WITH c, active_subscriptions, current_mrr, recent_support_tickets,
                    CASE 
                        WHEN recent_support_tickets = 0 THEN 30
                        WHEN recent_support_tickets <= 2 THEN 20
                        WHEN recent_support_tickets <= 5 THEN 10
                        ELSE 0
                    END +
                    CASE 
                        WHEN active_subscriptions > 0 THEN 30
                        ELSE 0
                    END +
                    CASE 
                        WHEN current_mrr > 500 THEN 40
                        WHEN current_mrr > 100 THEN 20
                        ELSE 0
                    END as health_score
                RETURN c.name, active_subscriptions, current_mrr, 
                        recent_support_tickets, health_score,
                        CASE 
                            WHEN health_score >= 80 THEN 'Healthy'
                            WHEN health_score >= 60 THEN 'Moderate'
                            WHEN health_score >= 40 THEN 'At Risk'
                            ELSE 'Critical'
                        END as health_status
                ORDER BY health_score DESC
                LIMIT 50
                """,
                "business_context": "Customer success prioritization"
            },
            {
                "id": "eval_038",
                "category": "Customer Management",
                "difficulty": "Medium",
                "question": "Identify expansion opportunities - customers with single products",
                "cypher": """
                MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s:Subscription {status: 'ACTIVE'})
                MATCH (s)-[:CONTAINS_ITEM]->(si:SubscriptionItem)-[:FOR_PRODUCT]->(p:Product)
                WITH c, s, count(DISTINCT p) as product_count, sum(si.total_price) as current_spend
                WHERE product_count = 1
                MATCH (all_products:Product {status: 'ACTIVE'})
                WITH c, s, current_spend, count(all_products) as total_available_products
                WHERE total_available_products > 1
                RETURN c.name, c.customerID, s.subscriptionID, 
                        current_spend as current_monthly_spend,
                        total_available_products - 1 as expansion_products_available,
                        current_spend * 1.5 as potential_expanded_spend
                ORDER BY current_spend DESC
                LIMIT 20
                """,
                "business_context": "Revenue expansion strategy"
            },
            {
                "id": "eval_039",
                "category": "Customer Management",
                "difficulty": "Hard",
                "question": "Analyze customer engagement patterns through support ticket types",
                "cypher": """
                MATCH (c:Customer)-[:RAISED_CASE]->(case:Case)-[:BELONGS_TO_CATEGORY]->(tc:TicketCategory)
                WHERE case.created_date >= date() - duration({months: 12})
                WITH c, tc.category_name as category, count(case) as ticket_count
                WITH c, 
                    collect({category: category, count: ticket_count}) as engagement_pattern,
                    sum(ticket_count) as total_tickets
                MATCH (c)-[:HAS_SUBSCRIPTION]->(s:Subscription {status: 'ACTIVE'})
                RETURN c.name, total_tickets, engagement_pattern,
                        sum(s.mrr) as monthly_revenue,
                        total_tickets / 12.0 as tickets_per_month,
                        CASE 
                            WHEN total_tickets = 0 THEN 'Silent'
                            WHEN total_tickets <= 6 THEN 'Low Engagement'
                            WHEN total_tickets <= 12 THEN 'Moderate Engagement'
                            ELSE 'High Engagement'
                        END as engagement_level
                ORDER BY tickets_per_month DESC
                LIMIT 30
                """,
                "business_context": "Customer relationship insights"
            },
            {
                "id": "eval_040",
                "category": "Customer Management",
                "difficulty": "Medium",
                "question": "Find customers with contract renewals due in the next 90 days",
                "cypher": """
                MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s:Subscription)
                WHERE s.end_date IS NOT NULL 
                  AND s.end_date >= date() 
                  AND s.end_date <= date() + duration({days: 90})
                  AND s.status = 'ACTIVE'
                OPTIONAL MATCH (s)-[:HAS_CONTRACT_TERMS]->(ct:ContractTerm)
                RETURN c.name, c.customerID, s.subscriptionID,
                        s.end_date as contract_end_date,
                        duration.between(date(), s.end_date).days as days_until_renewal,
                        s.mrr, s.arr,
                        ct.auto_renewal as has_auto_renewal
                ORDER BY days_until_renewal ASC
                """,
                "business_context": "Renewal management"
            },
            
            # CATEGORY 5: PERFORMANCE & OPTIMIZATION (Questions 41-45)
            {
                "id": "eval_041",
                "category": "Performance",
                "difficulty": "Hard",
                "question": "Identify the most complex customers by relationship count",
                "cypher": """
                MATCH (c:Customer)
                OPTIONAL MATCH (c)-[:HAS_SUBSCRIPTION]->(s:Subscription)
                OPTIONAL MATCH (c)-[:HAS_INVOICE]->(i:Invoice)
                OPTIONAL MATCH (c)-[:RAISED_CASE]->(case:Case)
                OPTIONAL MATCH (c)-[:HAS_CONTACT]->(contact:Contact)
                WITH c, count(DISTINCT s) as subscription_count,
                    count(DISTINCT i) as invoice_count,
                    count(DISTINCT case) as case_count,
                    count(DISTINCT contact) as contact_count
                WITH c, subscription_count + invoice_count + case_count + contact_count as total_relationships
                RETURN c.name, c.customerID, subscription_count, invoice_count, 
                        case_count, contact_count, total_relationships
                ORDER BY total_relationships DESC
                LIMIT 10
                """,
                "business_context": "System performance planning"
            },
            {
                "id": "eval_042",
                "category": "Performance",
                "difficulty": "Medium",
                "question": "Find potential data cleanup opportunities - inactive entities",
                "cypher": """
                WITH date() - duration({months: 12}) as cutoff_date
                MATCH (c:Customer)
                WHERE NOT EXISTS((c)-[:HAS_SUBSCRIPTION]->(:Subscription {status: 'ACTIVE'}))
                  AND NOT EXISTS((c)-[:HAS_INVOICE]->(i:Invoice) WHERE i.issue_date >= cutoff_date)
                  AND NOT EXISTS((c)-[:RAISED_CASE]->(case:Case) WHERE case.created_date >= cutoff_date)
                OPTIONAL MATCH (c)-[:HAS_SUBSCRIPTION]->(s:Subscription)
                OPTIONAL MATCH (c)-[:HAS_INVOICE]->(i:Invoice)
                RETURN c.customerID, c.name, c.created_date,
                        max(s.end_date) as last_subscription_end,
                        max(i.issue_date) as last_invoice_date,
                        duration.between(coalesce(max(i.issue_date), max(s.end_date), c.created_date), date()).months as months_inactive
                ORDER BY months_inactive DESC
                LIMIT 20
                """,
                "business_context": "Data archival planning"
            },
            {
                "id": "eval_043",
                "category": "Performance",
                "difficulty": "Hard",
                "question": "Analyze data volume by finding customers with the most invoice line items",
                "cypher": """
                MATCH (c:Customer)-[:HAS_INVOICE]->(i:Invoice)-[:CONTAINS_LINE]->(il:InvoiceLine)
                WITH c, count(il) as total_invoice_lines,
                    count(DISTINCT i) as total_invoices,
                    count(il) / count(DISTINCT i) as avg_lines_per_invoice
                RETURN c.name, c.customerID, total_invoices, total_invoice_lines, 
                        avg_lines_per_invoice,
                        CASE 
                            WHEN total_invoice_lines > 100 THEN 'High Volume'
                            WHEN total_invoice_lines > 50 THEN 'Medium Volume'
                            ELSE 'Low Volume'
                        END as data_volume_category
                ORDER BY total_invoice_lines DESC
                LIMIT 20
                """,
                "business_context": "Performance optimization planning"
            },
            {
                "id": "eval_044",
                "category": "Performance",
                "difficulty": "Medium",
                "question": "Check for potential duplicate customers based on email",
                "cypher": """
                MATCH (c1:Customer), (c2:Customer)
                WHERE c1.customerID < c2.customerID
                  AND c1.email = c2.email
                  AND c1.email IS NOT NULL
                RETURN c1.customerID, c1.name, c1.email,
                        c2.customerID, c2.name, c2.email,
                        'Email Match' as match_type
                ORDER BY c1.email
                """,
                "business_context": "Data quality management"
            },
            {
                "id": "eval_045",
                "category": "Performance",
                "difficulty": "Hard",
                "question": "Identify database hotspots - entities with highest relationship connectivity",
                "cypher": """
                MATCH (n)
                WITH n, labels(n)[0] as node_type, size((n)--()) as total_relationships
                WITH node_type, 
                    count(n) as entity_count,
                    avg(total_relationships) as avg_relationships,
                    max(total_relationships) as max_relationships,
                    sum(total_relationships) as total_relationships_sum
                RETURN node_type, entity_count, avg_relationships, max_relationships,
                        total_relationships_sum
                ORDER BY total_relationships_sum DESC
                """,
                "business_context": "System architecture optimization"
            },
            
            # CATEGORY 6: DATA INTEGRITY & VALIDATION (Questions 46-50)
            {
                "id": "eval_046",
                "category": "Data Integrity",
                "difficulty": "Medium",
                "question": "Validate referential integrity - invoice lines with valid invoice references",
                "cypher": """
                MATCH (il:InvoiceLine)
                WHERE il.invoiceID IS NOT NULL
                OPTIONAL MATCH (i:Invoice {invoiceID: il.invoiceID})
                WITH count(il) as total_lines, count(i) as valid_references
                RETURN total_lines, valid_references, 
                        total_lines - valid_references as orphaned_lines,
                        valid_references * 100.0 / total_lines as integrity_percentage
                """,
                "business_context": "Data quality assurance"
            },
            {
                "id": "eval_047",
                "category": "Data Integrity",
                "difficulty": "Hard",
                "question": "Check for business rule violations - invoices with future issue dates",
                "cypher": """
                MATCH (i:Invoice)
                WHERE i.issue_date > date()
                OPTIONAL MATCH (c:Customer)-[:HAS_INVOICE]->(i)
                RETURN i.invoiceID, i.invoiceNumber, i.issue_date, i.total_amount,
                        c.name as customer_name,
                        duration.between(date(), i.issue_date).days as days_in_future,
                        'Future Invoice Date' as violation_type
                ORDER BY days_in_future DESC
                """,
                "business_context": "Data validation and cleanup"
            },
            {
                "id": "eval_048",
                "category": "Data Integrity",
                "difficulty": "Medium",
                "question": "Validate currency consistency across customer transactions",
                "cypher": """
                MATCH (c:Customer)
                OPTIONAL MATCH (c)-[:HAS_INVOICE]->(i:Invoice)
                OPTIONAL MATCH (c)-[:HAS_SUBSCRIPTION]->(s:Subscription)
                WITH c, collect(DISTINCT i.currency) as invoice_currencies,
                    collect(DISTINCT s.currency) as subscription_currencies,
                    c.currency as customer_currency
                WITH c, customer_currency,
                    [currency IN invoice_currencies WHERE currency IS NOT NULL] as inv_curr,
                    [currency IN subscription_currencies WHERE currency IS NOT NULL] as sub_curr
                WHERE size(inv_curr) > 1 OR size(sub_curr) > 1
                RETURN c.name, c.customerID, customer_currency,
                        inv_curr as invoice_currencies,
                        sub_curr as subscription_currencies,
                        'Currency Inconsistency' as issue_type
                ORDER BY c.name
                LIMIT 20
                """,
                "business_context": "Financial data integrity"
            },
            {
                "id": "eval_049",
                "category": "Data Integrity",
                "difficulty": "Hard",
                "question": "Detect data anomalies - subscriptions with invalid date ranges",
                "cypher": """
                MATCH (s:Subscription)
                WHERE s.start_date > s.end_date AND s.end_date IS NOT NULL
                RETURN s.subscriptionID,
                        s.start_date,
                        s.end_date,
                        duration.between(s.end_date, s.start_date).days as invalid_days,
                        'Invalid Date Range' as anomaly_type
                ORDER BY invalid_days DESC
                """,
                "business_context": "Advanced data validation"
            },
            {
                "id": "eval_050",
                "category": "Data Integrity",
                "difficulty": "Hard",
                "question": "Comprehensive data quality score across all major entities",
                "cypher": """
                MATCH (c:Customer)
                WITH count(c) as total_customers,
                    count(CASE WHEN c.email IS NOT NULL THEN 1 END) as customers_with_email
                WITH total_customers, 
                    customers_with_email * 100.0 / total_customers as customer_email_completeness
                
                MATCH (i:Invoice)
                OPTIONAL MATCH (i)-[:CONTAINS_LINE]->(il:InvoiceLine)
                WITH customer_email_completeness,
                    count(i) as total_invoices,
                    count(CASE WHEN EXISTS((i)-[:CONTAINS_LINE]->()) THEN 1 END) as invoices_with_lines
                WITH customer_email_completeness,
                    invoices_with_lines * 100.0 / total_invoices as invoice_line_completeness
                
                MATCH (s:Subscription)
                WITH customer_email_completeness, invoice_line_completeness,
                    count(s) as total_subscriptions,
                    count(CASE WHEN s.mrr IS NOT NULL THEN 1 END) as subscriptions_with_mrr
                WITH customer_email_completeness, invoice_line_completeness,
                    subscriptions_with_mrr * 100.0 / total_subscriptions as subscription_mrr_completeness
                
                RETURN round(customer_email_completeness, 2) as customer_email_completeness,
                        round(invoice_line_completeness, 2) as invoice_line_completeness,
                        round(subscription_mrr_completeness, 2) as subscription_mrr_completeness,
                        round((customer_email_completeness + invoice_line_completeness + 
                                subscription_mrr_completeness) / 3, 2) as overall_data_quality_score
                """,
                "business_context": "Data governance and quality management"
            }
        ]
    
    def _execute_query(self, query_info: Dict[str, Any]) -> QueryResult:
        """Execute a single query and return results with timing"""
        start_time = time.time()
        
        try:
            with self.driver.session() as session:
                result = session.run(query_info["cypher"])
                records = [record.data() for record in result]
                execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                # Generate result summary
                summary = {
                    "record_count": len(records),
                    "has_data": len(records) > 0,
                    "first_record_keys": list(records[0].keys()) if records else [],
                    "execution_time_ms": execution_time
                }
                
                # Add specific analysis based on query type
                if records:
                    summary.update(self._analyze_query_results(query_info["id"], records))
                
                return QueryResult(
                    query_id=query_info["id"],
                    category=query_info["category"],
                    difficulty=query_info["difficulty"],
                    question=query_info["question"],
                    cypher_query=query_info["cypher"],
                    execution_time_ms=execution_time,
                    record_count=len(records),
                    success=True,
                    error_message=None,
                    result_data=records[:10],  # Store only first 10 records to avoid memory issues
                    result_summary=summary,
                    business_context=query_info["business_context"]
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Query {query_info['id']} failed: {e}")
            
            return QueryResult(
                query_id=query_info["id"],
                category=query_info["category"],
                difficulty=query_info["difficulty"],
                question=query_info["question"],
                cypher_query=query_info["cypher"],
                execution_time_ms=execution_time,
                record_count=0,
                success=False,
                error_message=str(e),
                result_data=[],
                result_summary={"error": str(e)},
                business_context=query_info["business_context"]
            )
    
    def _analyze_query_results(self, query_id: str, records: List[Dict]) -> Dict[str, Any]:
        """Provide specific analysis based on query type"""
        analysis = {}
        
        # Add query-specific analysis
        if query_id == "eval_001":  # Customer invoice counts
            if records:
                analysis["max_invoices"] = max(r.get("total_invoices", 0) for r in records)
                analysis["avg_invoices"] = sum(r.get("total_invoices", 0) for r in records) / len(records)
                
        elif query_id == "eval_026":  # MRR calculation
            if records and "total_mrr" in records[0]:
                analysis["total_mrr"] = records[0]["total_mrr"]
                analysis["projected_arr"] = records[0].get("projected_arr", 0)
                
        elif query_id == "eval_050":  # Data quality score
            if records:
                analysis["overall_quality_score"] = records[0].get("overall_data_quality_score", 0)
        
        return analysis
    
    def _get_database_info(self) -> Dict[str, Any]:
        """Get basic database information"""
        try:
            with self.driver.session() as session:
                # Get node counts
                node_result = session.run("""
                MATCH (n) 
                RETURN labels(n)[0] as node_type, count(*) as count 
                ORDER BY count DESC
                """)
                node_counts = {record["node_type"]: record["count"] for record in node_result}
                
                # Get relationship counts
                rel_result = session.run("""
                MATCH ()-[r]->() 
                RETURN type(r) as rel_type, count(*) as count 
                ORDER BY count DESC
                """)
                rel_counts = {record["rel_type"]: record["count"] for record in rel_result}
                
                return {
                    "node_counts": node_counts,
                    "relationship_counts": rel_counts,
                    "total_nodes": sum(node_counts.values()),
                    "total_relationships": sum(rel_counts.values())
                }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}
    
    def run_evaluation(self) -> EvaluationReport:
        """Run all evaluation queries and generate comprehensive report"""
        if not self.connect():
            raise Exception("Failed to connect to Neo4j database")
        
        try:
            logger.info("Starting Neo4j evaluation run...")
            start_time = time.time()
            
            # Get database information
            database_info = self._get_database_info()
            
            # Execute all queries
            query_results = []
            successful_queries = 0
            failed_queries = 0
            
            for i, query_info in enumerate(self.evaluation_queries, 1):
                logger.info(f"Executing query {i}/50: {query_info['id']} - {query_info['question'][:50]}...")
                
                result = self._execute_query(query_info)
                query_results.append(result)
                
                if result.success:
                    successful_queries += 1
                    logger.info(f"✓ Query {result.query_id} completed in {result.execution_time_ms:.2f}ms")
                else:
                    failed_queries += 1
                    logger.error(f"✗ Query {result.query_id} failed: {result.error_message}")
            
            total_execution_time = (time.time() - start_time) * 1000
            
            # Generate performance summary
            performance_summary = self._generate_performance_summary(query_results)
            
            # Generate data quality metrics
            data_quality_metrics = self._generate_data_quality_metrics(query_results)
            
            # Create evaluation report
            report = EvaluationReport(
                test_run_id=f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now().isoformat(),
                database_info=database_info,
                total_queries=len(self.evaluation_queries),
                successful_queries=successful_queries,
                failed_queries=failed_queries,
                total_execution_time_ms=total_execution_time,
                query_results=query_results,
                performance_summary=performance_summary,
                data_quality_metrics=data_quality_metrics
            )
            
            logger.info(f"Evaluation completed: {successful_queries}/{len(self.evaluation_queries)} queries successful")
            return report
            
        finally:
            self.close()
    
    def _generate_performance_summary(self, results: List[QueryResult]) -> Dict[str, Any]:
        """Generate performance analysis summary"""
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return {"error": "No successful queries to analyze"}
        
        execution_times = [r.execution_time_ms for r in successful_results]
        
        return {
            "avg_execution_time_ms": sum(execution_times) / len(execution_times),
            "min_execution_time_ms": min(execution_times),
            "max_execution_time_ms": max(execution_times),
            "queries_under_100ms": len([t for t in execution_times if t < 100]),
            "queries_under_1000ms": len([t for t in execution_times if t < 1000]),
            "slowest_queries": [
                {"query_id": r.query_id, "time_ms": r.execution_time_ms, "question": r.question}
                for r in sorted(successful_results, key=lambda x: x.execution_time_ms, reverse=True)[:5]
            ],
            "performance_by_category": self._analyze_performance_by_category(successful_results)
        }
    
    def _analyze_performance_by_category(self, results: List[QueryResult]) -> Dict[str, Any]:
        """Analyze performance by query category"""
        by_category = {}
        
        for result in results:
            if result.category not in by_category:
                by_category[result.category] = []
            by_category[result.category].append(result.execution_time_ms)
        
        return {
            category: {
                "avg_time_ms": sum(times) / len(times),
                "query_count": len(times),
                "max_time_ms": max(times)
            }
            for category, times in by_category.items()
        }
    
    def _generate_data_quality_metrics(self, results: List[QueryResult]) -> Dict[str, Any]:
        """Extract data quality insights from evaluation results"""
        metrics = {}
        
        # Find specific quality-related queries
        for result in results:
            if result.query_id == "eval_050" and result.success and result.result_data:
                metrics["overall_quality_score"] = result.result_data[0].get("overall_data_quality_score", 0)
                metrics["customer_email_completeness"] = result.result_data[0].get("customer_email_completeness", 0)
                metrics["invoice_line_completeness"] = result.result_data[0].get("invoice_line_completeness", 0)
                metrics["subscription_mrr_completeness"] = result.result_data[0].get("subscription_mrr_completeness", 0)
            
            elif result.query_id == "eval_008" and result.success:  # Invoices without lines
                metrics["invoices_without_lines"] = result.record_count
        return metrics

if __name__ == '__main__':
    # --- Configuration ---
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    # --- Evaluation Runner ---
    runner = Neo4jEvaluationRunner(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    report = runner.run_evaluation()
    
    # --- Save Report ---
    report_path = Path("evaluation_reports")
    report_path.mkdir(exist_ok=True)
    report_file = report_path / f"{report.test_run_id}.json"
    
    # Convert report to dict for JSON serialization
    report_dict = asdict(report)

    # Convert complex objects to string representations
    for result in report_dict['query_results']:
        for i, record in enumerate(result['result_data']):
            for key, value in record.items():
                if hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
        
    with open(report_file, "w") as f:
        json.dump(report_dict, f, indent=4)
        
    logger.info(f"Evaluation report saved to: {report_file}")

    # --- Generate Summary Markdown ---
    summary_md = f"""
# Evaluation Summary: {report.test_run_id}

- **Date**: {report.timestamp}
- **Total Queries**: {report.total_queries}
- **Successful**: {report.successful_queries}
- **Failed**: {report.failed_queries}
- **Total Time**: {report.total_execution_time_ms:.2f}ms

## Performance
- **Avg. Query Time**: {report.performance_summary.get('avg_execution_time_ms', 0):.2f}ms
- **Max. Query Time**: {report.performance_summary.get('max_execution_time_ms', 0):.2f}ms

## Data Quality
- **Overall Quality Score**: {report.data_quality_metrics.get('overall_quality_score', 'N/A')}
- **Invoices without Lines**: {report.data_quality_metrics.get('invoices_without_lines', 'N/A')}

See the full JSON report for detailed results: `{report_file}`
"""
    
    summary_file = report_path / f"{report.test_run_id}_summary.md"
    with open(summary_file, "w") as f:
        f.write(summary_md)
        
    logger.info(f"Summary report saved to: {summary_file}")
```