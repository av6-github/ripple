"""Demonstration Data Seeding & Environment Packaging Script for RIPPLE.

Provisions remote Supabase PostgreSQL and Neo4j AuraDB with representative
Polish SME borrower profiles, multi-year financial statements, synthetic
commercial trade counterparties (strictly labelled is_synthetic = True per Rule 4.4),
and initial credit assessment snapshots with human officer decision records.
"""

import argparse
import logging
import os
import uuid
from typing import Any, Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor

from backend.features.domain import FinancialStatementPeriod
from backend.graph.neo4j_client import Neo4jGraphClient
from backend.repositories.assessment_repository import AssessmentRepository
from backend.services.assessment_service import AssessmentService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ripple-seed")

DEMO_SMES = [
  {
    "name": "PolTech Solutions Sp. z o.o. [ID: PL-5219483011 | Role: Tier-1 Enterprise Tech & Cloud Core]",
    "tax_id": "PL-5219483011",
    "sector": "technology",
    "statements": [
      {
        "fiscal_year": 2023,
        "total_assets": 1200000.0,
        "current_assets": 650000.0,
        "cash_and_equivalents": 220000.0,
        "inventory": 50000.0,
        "accounts_receivable": 180000.0,
        "total_liabilities": 320000.0,
        "short_term_liabilities": 180000.0,
        "total_equity": 880000.0,
        "total_revenue": 1600000.0,
        "cost_of_goods_sold": 850000.0,
        "gross_profit": 750000.0,
        "operating_profit_ebit": 310000.0,
        "net_profit": 230000.0,
        "operating_cash_flow": 280000.0,
        "interest_expense": 12000.0,
      }
    ],
    "counterparties": [
      "CloudInfra Europe BV [ID: SUP-PL-01 | Role: Upstream Tier-1 Cloud Infrastructure Provider]",
      "MicroSilicon Fabrication S.A. [ID: SUP-PL-02 | Role: Upstream Semiconductor Hardware Vendor]",
      "Warsaw FinTech Services [ID: BYR-PL-01 | Role: Downstream Banking Software Client]",
      "Nordic Telecom Systems [ID: BYR-PL-02 | Role: Downstream Enterprise Telecom Buyer]",
      "Central European Data Hub [ID: PRT-PL-01 | Role: Strategic Regional Distribution Partner]",
    ],
    "decision": "APPROVE",
    "officer_notes": "Strong liquidity profile and zero long-term debt. Approved under standard prime SME facility.",
  },
  {
    "name": "Silesia Metalworks S.A. [ID: PL-6348192033 | Role: Heavy Industrial Metal Fabricator]",
    "tax_id": "PL-6348192033",
    "sector": "manufacturing",
    "statements": [
      {
        "fiscal_year": 2023,
        "total_assets": 850000.0,
        "current_assets": 320000.0,
        "cash_and_equivalents": 45000.0,
        "inventory": 110000.0,
        "accounts_receivable": 130000.0,
        "total_liabilities": 460000.0,
        "short_term_liabilities": 280000.0,
        "total_equity": 390000.0,
        "total_revenue": 950000.0,
        "cost_of_goods_sold": 680000.0,
        "gross_profit": 270000.0,
        "operating_profit_ebit": 85000.0,
        "net_profit": 42000.0,
        "operating_cash_flow": 60000.0,
        "interest_expense": 24000.0,
      }
    ],
    "counterparties": [
      "Katowice Metallurgical Coking [ID: SUP-SM-01 | Role: Raw Metallurgical Ore Supplier]",
      "Silesian Smelting Reagents [ID: SUP-SM-02 | Role: Industrial Heat & Chemical Reagents Vendor]",
      "Kraków Heavy Machinery [ID: BYR-SM-01 | Role: Heavy Equipment Manufacturer]",
      "Daimler Commercial Vehicles East [ID: BYR-SM-02 | Role: Commercial Vehicle OEM Buyer]",
      "Silesia Rail Haulage Sp. k. [ID: PRT-SM-01 | Role: Heavy Industrial Freight Logistics Partner]",
    ],
    "decision": "FURTHER_REVIEW",
    "officer_notes": "Moderate debt service coverage. Referred to credit committee for covenant structure review.",
  },
  {
    "name": "Mazovia Logistics Sp. k. [ID: PL-7013928174 | Role: Cold-Chain & Pan-European Freight Core]",
    "tax_id": "PL-7013928174",
    "sector": "transportation",
    "statements": [
      {
        "fiscal_year": 2023,
        "total_assets": 600000.0,
        "current_assets": 190000.0,
        "cash_and_equivalents": 25000.0,
        "inventory": 15000.0,
        "accounts_receivable": 140000.0,
        "total_liabilities": 380000.0,
        "short_term_liabilities": 260000.0,
        "total_equity": 220000.0,
        "total_revenue": 720000.0,
        "cost_of_goods_sold": 540000.0,
        "gross_profit": 180000.0,
        "operating_profit_ebit": 40000.0,
        "net_profit": 15000.0,
        "operating_cash_flow": 30000.0,
        "interest_expense": 18000.0,
      }
    ],
    "counterparties": [
      "Orlen Petrochemical Fleet Terminal [ID: SUP-ML-01 | Role: Primary Fleet Diesel & Fuel Supplier]",
      "Scania Commercial Fleet Leasing [ID: SUP-ML-02 | Role: Commercial Vehicle Fleet Lessor]",
      "Biedronka Retail Distribution [ID: BYR-ML-01 | Role: FMCG Supermarket Network Client]",
      "Pekao Pharmaceutical Cold Hub [ID: BYR-ML-02 | Role: Pharmaceutical Cold Storage Client]",
      "Mazovian Highway Maintenance Hub [ID: PRT-ML-01 | Role: Regional Vehicle Servicing Partner]",
    ],
    "decision": "FURTHER_REVIEW",
    "officer_notes": "Elongated DSO collection period creates working capital friction. Requires quarterly receivables covenant.",
  },
  {
    "name": "Baltic Retail Group Sp. z o.o. [ID: PL-5830192847 | Role: Regional Multi-Brand Retail Chain]",
    "tax_id": "PL-5830192847",
    "sector": "retail",
    "statements": [
      {
        "fiscal_year": 2023,
        "total_assets": 450000.0,
        "current_assets": 110000.0,
        "cash_and_equivalents": 9000.0,
        "inventory": 75000.0,
        "accounts_receivable": 20000.0,
        "total_liabilities": 430000.0,
        "short_term_liabilities": 340000.0,
        "total_equity": 20000.0,
        "total_revenue": 380000.0,
        "cost_of_goods_sold": 310000.0,
        "gross_profit": 70000.0,
        "operating_profit_ebit": -35000.0,
        "net_profit": -55000.0,
        "operating_cash_flow": -20000.0,
        "interest_expense": 22000.0,
      }
    ],
    "counterparties": [
      "Amber Coast Wholesale Distributors [ID: SUP-BR-01 | Role: FMCG Wholesale Confectionery Supplier]",
      "Vistula Packaging Solutions [ID: SUP-BR-02 | Role: Commercial Packaging & Paperboard Vendor]",
      "Pomeranian Consumer Cooperative [ID: BYR-BR-01 | Role: Municipal Retail Cooperative Buyer]",
      "Gdynia Port Supermarket Franchisees [ID: BYR-BR-02 | Role: Coastal Outlet Network Franchisee]",
      "Baltic Express Last-Mile Couriers [ID: PRT-BR-01 | Role: Regional E-Commerce Delivery Partner]",
    ],
    "decision": "REJECT",
    "officer_notes": "Severe leverage (D/E > 20x), operating loss, and negative cash flow. Application declined.",
  },
  {
    "name": "Kraków Precision Dynamics [ID: PL-6761928374 | Role: Aerospace & Defense CNC Engineering]",
    "tax_id": "PL-6761928374",
    "sector": "engineering",
    "statements": [
      {
        "fiscal_year": 2023,
        "total_assets": 780000.0,
        "current_assets": 360000.0,
        "cash_and_equivalents": 85000.0,
        "inventory": 65000.0,
        "accounts_receivable": 150000.0,
        "total_liabilities": 290000.0,
        "short_term_liabilities": 160000.0,
        "total_equity": 490000.0,
        "total_revenue": 1050000.0,
        "cost_of_goods_sold": 680000.0,
        "gross_profit": 370000.0,
        "operating_profit_ebit": 160000.0,
        "net_profit": 115000.0,
        "operating_cash_flow": 140000.0,
        "interest_expense": 14000.0,
      }
    ],
    "counterparties": [
      "AeroTitanium Certified Alloys [ID: SUP-KP-01 | Role: Certified Titanium Aerospace Alloy Supplier]",
      "OptoLaser Sensor Components [ID: SUP-KP-02 | Role: High-Precision Laser Sensor Vendor]",
      "Airbus Defence Systems Poland [ID: BYR-KP-01 | Role: Aerospace Defense Prime Contractor]",
      "Lufthansa Technik Overhaul Kraków [ID: BYR-KP-02 | Role: Aircraft Maintenance & Overhaul Client]",
      "Kraków University Materials Testing Labs [ID: PRT-KP-01 | Role: Certified R&D Materials Testing Partner]",
    ],
    "decision": "APPROVE",
    "officer_notes": "High margins, healthy debt coverage, and solid operating cash flows. Facility approved.",
  },
]


def seed_demo_environment(reset: bool = False):
    """Seed remote databases with demo data."""
    logger.info("Initializing RIPPLE Demo Environment Seeder...")
    repo = AssessmentRepository()
    service = AssessmentService(assessment_repo=repo)
    neo4j_client = Neo4jGraphClient()

    officer_id = "00000000-0000-0000-0000-000000000001"
    repo.ensure_officer_user(officer_id, email="lead_officer@bank.pl")
    repo.ensure_model_registered("v1.0.0")

    created_smes = []

    for item in DEMO_SMES:
        logger.info(f"Processing SME: {item['name']} ({item['tax_id']})")
        # 1. Upsert SME Profile in PostgreSQL
        sme = repo.create_sme_profile(
            name=item["name"],
            tax_identifier=item["tax_id"],
            sector=item["sector"],
        )
        sme_id = sme["id"]
        created_smes.append(sme_id)

        # 2. Ingest Statements into Feature Period
        periods = [FinancialStatementPeriod(**stmt) for stmt in item["statements"]]

        # 3. Create Synthetic Network Counterparties in Neo4j (Rule 4.4 strictly enforced)
        edges = []
        counterparties = item.get("counterparties", [])
        for i, c_name in enumerate(counterparties):
            # Enforce is_synthetic = True on every commercial trade relationship
            try:
                neo4j_client.upsert_commercial_relation(
                    source_id=item["tax_id"],
                    target_id=c_name,
                    rel_type="SUPPLIES_TO" if i % 2 == 0 else "BUYS_FROM",
                    annual_volume=75_000.0 + (i * 25000.0),
                    tenure_months=24 + (i * 6),
                    is_synthetic=True,
                )
            except Exception as e:
                logger.warning(f"Neo4j relation upsert failed (non-critical): {e}")

            edges.append([0, i + 1])
            edges.append([i + 1, 0])

        # Add cross-edges among counterparties for richer topology (>= 5 nodes)
        if len(counterparties) >= 4:
            edges.append([1, 2])
            edges.append([2, 1])
            edges.append([3, 4])
            edges.append([4, 3])

        # 4. Execute Full Multi-Modal Risk Assessment
        try:
            res = service.run_assessment(
                sme_id=sme_id,
                statement_periods=periods,
                officer_id=officer_id,
                network_neighbors=counterparties if counterparties else None,
                network_edges=edges if edges else None,
            )
            assessment_id = res["assessment_id"]
            logger.info(
                f"  -> Assessment Run: ID={assessment_id[:8]} | Fused PD={(res['fused_pd']*100):.2f}% | "
                f"Risk Band={res['risk_band']} | Recommendation={res['recommendation']}"
            )

            # 5. Record Human Bank Officer Credit Decision (Rule 4.6)
            is_override = False
            rec_str = res["recommendation"]
            if rec_str == "HIGHER_RISK" and item["decision"] == "APPROVE":
                is_override = True
                decision_val = "OVERRIDE_APPROVE"
            elif rec_str == "LOWER_RISK" and item["decision"] == "REJECT":
                is_override = True
                decision_val = "OVERRIDE_REJECT"
            else:
                decision_val = item["decision"]

            repo.record_officer_decision(
                assessment_id=assessment_id,
                officer_id=officer_id,
                decision=decision_val,
                is_override=is_override,
                override_reason="Compensating collateral and historical banking relationship" if is_override else None,
                comments=item["officer_notes"],
            )
            logger.info(f"  -> Officer Decision Recorded: {decision_val} (Override={is_override})")

        except Exception as e:
            logger.error(f"  -> Assessment failed for {item['name']}: {e}", exc_info=True)

    neo4j_client.close()
    logger.info(f"Successfully seeded {len(created_smes)} Polish benchmark SMEs and multi-modal dossiers!")
    return created_smes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed RIPPLE demonstration environment")
    parser.add_argument("--reset", action="store_true", help="Reset existing test records")
    args = parser.parse_args()

    seed_demo_environment(reset=args.reset)
