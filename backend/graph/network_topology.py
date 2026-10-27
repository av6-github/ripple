"""Ego-network graph topology and edge construction utilities for RIPPLE.

Constructs realistic, natural supply-chain mesh topologies based on counterparty
commercial roles (incoming suppliers, outgoing buyers, bidirectional partners,
and inter-counterparty Tier-2 / fulfillment cross links).
"""

from typing import Any, Dict, List


def is_supplier(cp: Dict[str, Any]) -> bool:
    direction = (cp.get("direction") or "").lower()
    role = (cp.get("role") or cp.get("type") or "").lower()
    nid = str(cp.get("id") or "").lower()
    return (
        direction == "incoming"
        or "supplier" in role
        or "vendor" in role
        or "provider" in role
        or "upstream" in role
        or "lessor" in role
        or nid.startswith("sup-")
    )


def is_partner(cp: Dict[str, Any]) -> bool:
    direction = (cp.get("direction") or "").lower()
    role = (cp.get("role") or cp.get("type") or "").lower()
    nid = str(cp.get("id") or "").lower()
    return (
        direction == "bidirectional"
        or "partner" in role
        or "hub" in role
        or "lab" in role
        or nid.startswith("prt-")
    )


def is_buyer(cp: Dict[str, Any]) -> bool:
    return not is_supplier(cp) and not is_partner(cp)


def build_ego_network_edges(counterparties: List[Dict[str, Any]]) -> List[List[int]]:
    """Construct realistic commercial network edges between Target SME (node 0) and counterparties (nodes 1..N).

    Also creates authentic inter-counterparty cross-edges (Tier-2 component supply,
    fulfillment logistics links, and buyer consortiums) rather than static star topologies.
    """
    if not counterparties:
        return []

    edges: List[List[int]] = []

    # 1. Primary trade edges between Target SME (node 0) and each counterparty
    for idx, cp in enumerate(counterparties):
        node_id = idx + 1
        if is_supplier(cp):
            # Upstream trade: supplier -> SME
            edges.append([node_id, 0])
            edges.append([0, node_id])
        elif is_buyer(cp):
            # Downstream trade: SME -> buyer
            edges.append([0, node_id])
            edges.append([node_id, 0])
        else:
            # Partner / joint venture
            edges.append([0, node_id])
            edges.append([node_id, 0])

    # 2. Inter-counterparty cross edges
    sup_nodes = [i + 1 for i, cp in enumerate(counterparties) if is_supplier(cp)]
    byr_nodes = [i + 1 for i, cp in enumerate(counterparties) if is_buyer(cp)]
    prt_nodes = [i + 1 for i, cp in enumerate(counterparties) if is_partner(cp)]

    # Tier-2 supply chain mesh: upstream raw material suppliers sell into sub-assembly suppliers
    if len(sup_nodes) >= 2:
        edges.append([sup_nodes[0], sup_nodes[1]])
        edges.append([sup_nodes[1], sup_nodes[0]])
    if len(sup_nodes) >= 3:
        edges.append([sup_nodes[1], sup_nodes[2]])
        edges.append([sup_nodes[2], sup_nodes[1]])

    # Logistics fulfillment links: partner hubs connect directly to primary enterprise buyers
    if len(prt_nodes) >= 1 and len(byr_nodes) >= 1:
        edges.append([prt_nodes[0], byr_nodes[0]])
        edges.append([byr_nodes[0], prt_nodes[0]])

    # Downstream cross-trade / consortium
    if len(byr_nodes) >= 3:
        edges.append([byr_nodes[0], byr_nodes[2]])
        edges.append([byr_nodes[2], byr_nodes[0]])

    # Deduplicate edges while preserving order
    seen = set()
    unique_edges: List[List[int]] = []
    for u, v in edges:
        pair = (u, v)
        if pair not in seen:
            seen.add(pair)
            unique_edges.append([u, v])

    return unique_edges
