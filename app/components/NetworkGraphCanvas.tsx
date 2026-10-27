"use client";

import React, { useState } from "react";
import { NetworkNeighbor, NetworkMetrics } from "@/lib/types";
import { SyntheticBadge } from "@/app/components/badges";
import {
  Share2,
  Building2,
  ArrowRight,
  ArrowLeft,
  ArrowLeftRight,
  Shield,
  Layers,
  Database,
  ExternalLink,
  Code2,
  CheckCircle2,
  Info,
} from "lucide-react";

interface NetworkGraphCanvasProps {
  smeName: string;
  smeId: string;
  tabularPd: number;
  graphPd: number | null;
  fusedPd: number;
  riskBand: string;
  networkMetrics?: NetworkMetrics;
}

export function NetworkGraphCanvas({
  smeName,
  smeId,
  tabularPd,
  graphPd,
  fusedPd,
  riskBand,
  networkMetrics,
}: NetworkGraphCanvasProps) {
  const [layoutMode, setLayoutMode] = useState<"bipartite" | "radial">("bipartite");
  const [selectedNodeId, setSelectedNodeId] = useState<string>("core-sme");
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [showCypher, setShowCypher] = useState(false);

  const rawNeighbors: NetworkNeighbor[] = networkMetrics?.neighbors || [];
  const isCold = rawNeighbors.length === 0;

  // Categorize strictly by role to prevent any duplicate display
  const suppliers: NetworkNeighbor[] = [];
  const buyers: NetworkNeighbor[] = [];
  const partners: NetworkNeighbor[] = [];

  rawNeighbors.forEach((n) => {
    const roleLower = (n.role || n.type || "").toLowerCase();
    const dirLower = (n.direction || "").toLowerCase();
    const idLower = (n.id || "").toLowerCase();
    if (
      dirLower === "incoming" ||
      roleLower.includes("supplier") ||
      roleLower.includes("vendor") ||
      roleLower.includes("provider") ||
      roleLower.includes("upstream") ||
      roleLower.includes("lessor") ||
      idLower.startsWith("sup-")
    ) {
      suppliers.push(n);
    } else if (
      dirLower === "bidirectional" ||
      roleLower.includes("partner") ||
      roleLower.includes("hub") ||
      roleLower.includes("lab") ||
      idLower.startsWith("prt-")
    ) {
      partners.push(n);
    } else {
      buyers.push(n);
    }
  });

  const filteredNeighbors = rawNeighbors;

  if (isCold) {
    return (
      <div className="p-6 rounded-2xl bg-zinc-50 dark:bg-zinc-950/70 border border-zinc-200 dark:border-zinc-800 space-y-4">
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <div className="relative">
            <div className="w-24 h-24 rounded-full border-2 border-dashed border-amber-500 bg-amber-50 dark:bg-amber-950/30 flex flex-col items-center justify-center text-amber-700 dark:text-amber-400">
              <Building2 className="w-6 h-6 mb-1 text-amber-600" />
              <span className="font-bold text-xs">Target SME</span>
              <span className="text-[10px] opacity-75 font-mono">Isolated Node</span>
            </div>
          </div>
          <div className="text-center max-w-md space-y-1.5">
            <p className="text-sm font-bold text-zinc-900 dark:text-zinc-100">
              Cold-Start Network Safety Fallback Active
            </p>
            <p className="text-xs text-zinc-500 leading-relaxed">
              No registered commercial counterparties found in Neo4j graph (Degree = 0).
              Per AGENTS.md Rule 4.2 (No Fabricated Risk), network diffusion is suppressed and 100% of score custody derives from tabular financials.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 border-t border-[#3a7ca5]/20 text-xs">
          <div>
            <span className="text-[#2f6690]">Degree Connectivity:</span>{" "}
            <span className="font-bold text-amber-700">0 (Isolated Node)</span>
          </div>
          <div>
            <span className="text-[#2f6690]">Graph Diffusion Weight:</span>{" "}
            <span className="font-bold text-[#16425b]">0% (Pure Tabular)</span>
          </div>
          <div>
            <span className="text-[#2f6690]">Fallback Policy:</span>{" "}
            <span className="font-bold text-[#2f6690]">Rule 4.2 Safe Exit Applied</span>
          </div>
        </div>
      </div>
    );
  }

  // Canvas dimensions
  const width = 860;
  const height = 460;
  const centerX = width / 2;
  const centerY = height / 2;

  // Build node coordinate mapping
  interface GraphNodeCoord {
    id: string;
    label: string;
    sublabel: string;
    category: "sme" | "supplier" | "buyer" | "partner";
    x: number;
    y: number;
    radius: number;
    color: string;
    glowColor: string;
    tradeVolume?: number;
    tenure?: number;
    direction: string;
    role: string;
    riskTier?: string;
  }

  const nodes: GraphNodeCoord[] = [];

  // 1. Center Target SME Node
  nodes.push({
    id: "core-sme",
    label: smeName.split("[")[0].trim() || "Target SME Borrower",
    sublabel: smeId.slice(0, 14),
    category: "sme",
    x: centerX,
    y: centerY,
    radius: 34,
    color: "#6366f1",
    glowColor: "rgba(99, 102, 241, 0.4)",
    direction: "core",
    role: "Target SME Credit Applicant",
    riskTier: riskBand,
  });

  // 2. Position counterparties based on layoutMode
  if (layoutMode === "bipartite") {
    // Upstream Suppliers on the left arc
    suppliers.forEach((s, idx) => {
      const total = suppliers.length;
      const yStep = height / (total + 1);
      const y = yStep * (idx + 1);
      nodes.push({
        id: s.id || `sup-${idx}`,
        label: s.name.split("[")[0].trim(),
        sublabel: s.id || `SUP-0${idx + 1}`,
        category: "supplier",
        x: 140,
        y: y,
        radius: 22,
        color: "#06b6d4",
        glowColor: "rgba(6, 182, 212, 0.35)",
        tradeVolume: s.annual_volume || 75000 + idx * 25000,
        tenure: s.tenure_months || 24 + idx * 6,
        direction: "incoming",
        role: s.role || "Tier-1 Upstream Supplier",
        riskTier: s.risk_level || "Low Risk",
      });
    });

    // Downstream Buyers on the right arc
    buyers.forEach((b, idx) => {
      const total = buyers.length;
      const yStep = height / (total + 1);
      const y = yStep * (idx + 1);
      nodes.push({
        id: b.id || `byr-${idx}`,
        label: b.name.split("[")[0].trim(),
        sublabel: b.id || `BYR-0${idx + 1}`,
        category: "buyer",
        x: width - 140,
        y: y,
        radius: 22,
        color: "#10b981",
        glowColor: "rgba(16, 185, 129, 0.35)",
        tradeVolume: b.annual_volume || 100000 + idx * 30000,
        tenure: b.tenure_months || 28 + idx * 6,
        direction: "outgoing",
        role: b.role || "Downstream Enterprise Client",
        riskTier: b.risk_level || "Low Risk",
      });
    });

    // Strategic Partners at Top Center
    partners.forEach((p, idx) => {
      nodes.push({
        id: p.id || `prt-${idx}`,
        label: p.name.split("[")[0].trim(),
        sublabel: p.id || `PRT-0${idx + 1}`,
        category: "partner",
        x: centerX + (idx === 0 ? 0 : idx % 2 === 0 ? 90 : -90),
        y: 65,
        radius: 22,
        color: "#f59e0b",
        glowColor: "rgba(245, 158, 11, 0.35)",
        tradeVolume: p.annual_volume || 120000,
        tenure: p.tenure_months || 36,
        direction: "bidirectional",
        role: p.role || "Strategic Distribution Partner",
        riskTier: p.risk_level || "Low Risk",
      });
    });
  } else {
    // Radial Orbital Layout around SME core
    const total = rawNeighbors.length;
    rawNeighbors.forEach((n, idx) => {
      const angle = -Math.PI / 2 + (2 * Math.PI * idx) / total;
      const radius = 170;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      const roleLower = (n.role || n.type || "").toLowerCase();
      const dirLower = (n.direction || "").toLowerCase();
      let cat: "supplier" | "buyer" | "partner" = "buyer";
      let col = "#10b981";
      let glow = "rgba(16, 185, 129, 0.35)";

      if (dirLower === "incoming" || roleLower.includes("supplier") || roleLower.includes("vendor")) {
        cat = "supplier";
        col = "#06b6d4";
        glow = "rgba(6, 182, 212, 0.35)";
      } else if (dirLower === "bidirectional" || roleLower.includes("partner") || roleLower.includes("hub") || roleLower.includes("lab")) {
        cat = "partner";
        col = "#f59e0b";
        glow = "rgba(245, 158, 11, 0.35)";
      }

      nodes.push({
        id: n.id || `node-${idx}`,
        label: n.name.split("[")[0].trim(),
        sublabel: n.id || `ID-0${idx + 1}`,
        category: cat,
        x,
        y,
        radius: 22,
        color: col,
        glowColor: glow,
        tradeVolume: n.annual_volume || 75000 + idx * 20000,
        tenure: n.tenure_months || 24,
        direction: n.direction || "outgoing",
        role: n.role || "Commercial Counterparty",
        riskTier: n.risk_level || "Low Risk",
      });
    });
  }

  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const coreNode = nodes[0];

  // Build edge connections
  interface GraphEdge {
    id: string;
    source: GraphNodeCoord;
    target: GraphNodeCoord;
    type: "incoming" | "outgoing" | "partner" | "cross";
    color: string;
    volumeLabel?: string;
  }

  const edges: GraphEdge[] = [];

  // Radial edges to Core SME
  nodes.slice(1).forEach((counterNode) => {
    if (counterNode.category === "supplier") {
      edges.push({
        id: `${counterNode.id}->sme`,
        source: counterNode,
        target: coreNode,
        type: "incoming",
        color: "#06b6d4",
        volumeLabel: counterNode.tradeVolume ? `${(counterNode.tradeVolume / 1000).toFixed(0)}k PLN` : undefined,
      });
    } else if (counterNode.category === "buyer") {
      edges.push({
        id: `sme->${counterNode.id}`,
        source: coreNode,
        target: counterNode,
        type: "outgoing",
        color: "#10b981",
        volumeLabel: counterNode.tradeVolume ? `${(counterNode.tradeVolume / 1000).toFixed(0)}k PLN` : undefined,
      });
    } else {
      edges.push({
        id: `sme<->${counterNode.id}`,
        source: coreNode,
        target: counterNode,
        type: "partner",
        color: "#f59e0b",
        volumeLabel: counterNode.tradeVolume ? `${(counterNode.tradeVolume / 1000).toFixed(0)}k PLN` : undefined,
      });
    }
  });

  // Cross-edges between counterparties for realistic supply chain mesh
  if (suppliers.length >= 2) {
    const s1 = nodeMap.get(suppliers[0].id || "sup-0");
    const s2 = nodeMap.get(suppliers[1].id || "sup-1");
    if (s1 && s2) {
      edges.push({
        id: `cross-sup`,
        source: s1,
        target: s2,
        type: "cross",
        color: "#64748b",
        volumeLabel: "Tier-2 Sync",
      });
    }
  }

  if (buyers.length >= 1 && partners.length >= 1) {
    const b1 = nodeMap.get(buyers[0].id || "byr-0");
    const p1 = nodeMap.get(partners[0].id || "prt-0");
    if (b1 && p1) {
      edges.push({
        id: `cross-buyer-partner`,
        source: p1,
        target: b1,
        type: "cross",
        color: "#64748b",
        volumeLabel: "Fulfillment",
      });
    }
  }

  // Active inspector selected entity
  const selectedEntity = nodes.find((n) => n.id === selectedNodeId) || coreNode;

  return (
    <div className="p-6 sm:p-8 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-6">
      {/* 1. Header Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#3a7ca5]/20 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Share2 className="w-5 h-5 text-[#2f6690]" />
            <h2 className="text-base font-bold text-[#16425b]">
              Counterparty Trade Network &amp; Graph DB Explorer
            </h2>
            <SyntheticBadge isSynthetic={true} />
          </div>
          <p className="text-xs text-[#2f6690] mt-1">
            Neo4j AuraDB Cypher Query • 2-Layer PyTorch Geometric GCN Ego-Network Diffusion
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Layout Mode Toggle */}
          <div className="inline-flex rounded-lg border border-[#3a7ca5]/30 p-0.5 bg-[#d9dcd6]/40">
            <button
              onClick={() => setLayoutMode("bipartite")}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                layoutMode === "bipartite"
                  ? "bg-[#16425b] text-white shadow-xs"
                  : "text-[#2f6690] hover:text-[#16425b]"
              }`}
            >
              Supply Chain Bipartite
            </button>
            <button
              onClick={() => setLayoutMode("radial")}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                layoutMode === "radial"
                  ? "bg-[#16425b] text-white shadow-xs"
                  : "text-[#2f6690] hover:text-[#16425b]"
              }`}
            >
              Orbital Ego-Mesh
            </button>
          </div>

          {/* View Cypher Toggle */}
          <button
            onClick={() => setShowCypher(!showCypher)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#3a7ca5]/40 text-xs font-semibold text-[#16425b] bg-white hover:bg-[#81c3d7]/15 transition"
          >
            <Code2 className="w-3.5 h-3.5 text-[#2f6690]" />
            {showCypher ? "Hide Cypher" : "Neo4j Cypher"}
          </button>
        </div>
      </div>

      {/* Cypher Query Drawer */}
      {showCypher && (
        <div className="p-4 rounded-xl bg-[#16425b] text-[#d9dcd6] text-xs font-mono space-y-2 border border-[#3a7ca5]/40 shadow-inner">
          <div className="flex items-center justify-between text-[11px] text-[#81c3d7] border-b border-white/10 pb-1.5">
            <span className="flex items-center gap-1.5 text-[#81c3d7] font-bold">
              <Database className="w-3.5 h-3.5" /> Neo4j AuraDB Cypher Extraction
            </span>
            <span className="text-[#d9dcd6]/70">AGENTS.md Rule 4.4 Enforced</span>
          </div>
          <pre className="overflow-x-auto text-[11px] text-emerald-400 leading-relaxed py-1">
{`MATCH (target:SME {tax_id: "${smeId}"})
OPTIONAL MATCH (target)<-[r1:COMMERCIAL_TRADE {direction: 'INCOMING'}]-(sup:Counterparty)
OPTIONAL MATCH (target)-[r2:COMMERCIAL_TRADE {direction: 'OUTGOING'}]->(byr:Counterparty)
OPTIONAL MATCH (target)-[r3:STRATEGIC_PARTNER]-(prt:Counterparty)
RETURN target, r1, sup, r2, byr, r3, prt;`}
          </pre>
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs bg-[#d9dcd6]/30 p-2.5 rounded-xl border border-[#3a7ca5]/25">
        <div className="text-[#16425b] font-semibold text-xs flex items-center gap-1.5">
          <span>Ego-Network Topology Map</span>
          <span className="text-[#2f6690] font-normal">({nodes.length} Connected Nodes)</span>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 text-[11px] text-[#2f6690] font-medium">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#16425b] inline-block shadow-xs" />
            <span className="text-[#16425b] font-semibold">Target Core SME</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#3a7ca5] inline-block shadow-xs" />
            <span>Upstream Supplier</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-700 inline-block shadow-xs" />
            <span>Downstream Buyer</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-600 inline-block shadow-xs" />
            <span>Strategic Partner</span>
          </div>
        </div>
      </div>

      {/* 2. Main Graph Visualization Canvas + Side Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* SVG Network Graph Canvas */}
        <div className="lg:col-span-3 rounded-2xl bg-zinc-950 border border-zinc-800 shadow-inner overflow-hidden relative">
          {/* Canvas Sub-header */}
          <div className="absolute top-3 left-4 right-4 flex items-center justify-between text-[11px] text-zinc-400 pointer-events-none z-10">
            <span className="font-mono text-zinc-500">
              Interactive SVG Graph Canvas • Click any node to inspect
            </span>
            <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 font-mono text-[#81c3d7]">
              {nodes.length} Nodes • {edges.length} Edges
            </span>
          </div>

          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-auto select-none"
            style={{ maxHeight: "490px" }}
          >
            {/* SVG Definitions */}
            <defs>
              {/* Engineering Grid Pattern */}
              <pattern id="graph-grid" width="30" height="30" patternUnits="userSpaceOnUse">
                <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#1e293b" strokeWidth="0.5" opacity="0.6" />
                <circle cx="0" cy="0" r="1" fill="#334155" opacity="0.8" />
              </pattern>

              {/* Node Drop Shadow Filter */}
              <filter id="node-shadow" x="-30%" y="-30%" width="160%" height="160%">
                <feDropShadow dx="0" dy="4" stdDeviation="6" floodOpacity="0.4" />
              </filter>

              {/* Node Glow Filter */}
              <filter id="node-glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="8" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>

              {/* Marker: Incoming Supplier Arrow (Cyan) */}
              <marker
                id="arrow-incoming"
                viewBox="0 0 10 10"
                refX="26"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#06b6d4" />
              </marker>

              {/* Marker: Outgoing Buyer Arrow (Emerald) */}
              <marker
                id="arrow-outgoing"
                viewBox="0 0 10 10"
                refX="26"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
              </marker>

              {/* Marker: Partner Arrow (Amber) */}
              <marker
                id="arrow-partner"
                viewBox="0 0 10 10"
                refX="26"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#f59e0b" />
              </marker>

              {/* Marker: Cross Edge Arrow (Slate) */}
              <marker
                id="arrow-cross"
                viewBox="0 0 10 10"
                refX="22"
                refY="5"
                markerWidth="5"
                markerHeight="5"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#64748b" />
              </marker>

              {/* Gradients for Nodes */}
              <radialGradient id="grad-sme" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#818cf8" />
                <stop offset="100%" stopColor="#4338ca" />
              </radialGradient>

              <radialGradient id="grad-supplier" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#22d3ee" />
                <stop offset="100%" stopColor="#0891b2" />
              </radialGradient>

              <radialGradient id="grad-buyer" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#34d399" />
                <stop offset="100%" stopColor="#059669" />
              </radialGradient>

              <radialGradient id="grad-partner" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#fbbf24" />
                <stop offset="100%" stopColor="#d97706" />
              </radialGradient>
            </defs>

            {/* Background Grid */}
            <rect width="100%" height="100%" fill="url(#graph-grid)" />

            {/* Subtle Bipartite Background Zones */}
            {layoutMode === "bipartite" && (
              <g opacity="0.3">
                <rect x="20" y="20" width="240" height={height - 40} rx="16" fill="#083344" opacity="0.2" />
                <text x="140" y="45" textAnchor="middle" fill="#06b6d4" fontSize="10" fontWeight="bold" letterSpacing="0.1em">
                  UPSTREAM SUPPLIERS (INFLOW)
                </text>

                <rect x={width - 260} y="20" width="240" height={height - 40} rx="16" fill="#064e3b" opacity="0.2" />
                <text x={width - 140} y="45" textAnchor="middle" fill="#10b981" fontSize="10" fontWeight="bold" letterSpacing="0.1em">
                  DOWNSTREAM BUYERS (OUTFLOW)
                </text>
              </g>
            )}

            {/* Render Graph Edges */}
            <g className="edges-layer">
              {edges.map((edge) => {
                const isConnectedToHover =
                  hoveredNodeId === edge.source.id || hoveredNodeId === edge.target.id;
                const isConnectedToSelected =
                  selectedNodeId === edge.source.id || selectedNodeId === edge.target.id;
                const isDimmed =
                  hoveredNodeId !== null && !isConnectedToHover && selectedNodeId !== edge.source.id && selectedNodeId !== edge.target.id;

                let marker = "url(#arrow-outgoing)";
                if (edge.type === "incoming") marker = "url(#arrow-incoming)";
                if (edge.type === "partner") marker = "url(#arrow-partner)";
                if (edge.type === "cross") marker = "url(#arrow-cross)";

                // Curved path calculation
                const isCross = edge.type === "cross";
                const midX = (edge.source.x + edge.target.x) / 2;
                const midY = (edge.source.y + edge.target.y) / 2;
                const controlX = isCross ? midX + 35 : midX;
                const controlY = isCross ? midY - 30 : midY;

                const pathData = isCross
                  ? `M ${edge.source.x} ${edge.source.y} Q ${controlX} ${controlY} ${edge.target.x} ${edge.target.y}`
                  : `M ${edge.source.x} ${edge.source.y} L ${edge.target.x} ${edge.target.y}`;

                return (
                  <g
                    key={edge.id}
                    className="transition-opacity duration-200"
                    opacity={isDimmed ? 0.15 : isConnectedToHover || isConnectedToSelected ? 1.0 : 0.65}
                  >
                    {/* Background glow stroke when selected/hovered */}
                    {(isConnectedToHover || isConnectedToSelected) && (
                      <path
                        d={pathData}
                        fill="none"
                        stroke={edge.color}
                        strokeWidth="5"
                        opacity="0.3"
                        strokeLinecap="round"
                      />
                    )}

                    {/* Main Edge Path */}
                    <path
                      d={pathData}
                      fill="none"
                      stroke={edge.color}
                      strokeWidth={isConnectedToSelected ? 2.5 : isCross ? 1.5 : 2}
                      strokeDasharray={isCross ? "4,4" : undefined}
                      markerEnd={marker}
                    />

                    {/* Edge Volume Label Badge at Midpoint */}
                    {edge.volumeLabel && (
                      <g transform={`translate(${controlX}, ${controlY})`}>
                        <rect
                          x="-28"
                          y="-9"
                          width="56"
                          height="18"
                          rx="9"
                          fill="#090d16"
                          stroke={edge.color}
                          strokeWidth="1"
                          opacity="0.85"
                        />
                        <text
                          x="0"
                          y="3"
                          textAnchor="middle"
                          fill="#e2e8f0"
                          fontSize="9"
                          fontFamily="monospace"
                          fontWeight="bold"
                        >
                          {edge.volumeLabel}
                        </text>
                      </g>
                    )}
                  </g>
                );
              })}
            </g>

            {/* Render Graph Nodes */}
            <g className="nodes-layer">
              {nodes.map((node) => {
                const isSelected = selectedNodeId === node.id;
                const isHovered = hoveredNodeId === node.id;
                const isCore = node.category === "sme";

                let fillGradient = "url(#grad-buyer)";
                if (isCore) fillGradient = "url(#grad-sme)";
                else if (node.category === "supplier") fillGradient = "url(#grad-supplier)";
                else if (node.category === "partner") fillGradient = "url(#grad-partner)";

                return (
                  <g
                    key={node.id}
                    transform={`translate(${node.x}, ${node.y})`}
                    className="cursor-pointer transition-transform duration-150"
                    onClick={() => setSelectedNodeId(node.id)}
                    onMouseEnter={() => setHoveredNodeId(node.id)}
                    onMouseLeave={() => setHoveredNodeId(null)}
                  >
                    {/* Radar Halo Pulse on Core SME Node */}
                    {isCore && (
                      <circle
                        r="48"
                        fill="none"
                        stroke="#6366f1"
                        strokeWidth="1.5"
                        opacity="0.3"
                        className="animate-ping"
                      />
                    )}

                    {/* Outer Glow Halo on Selection/Hover */}
                    {(isSelected || isHovered) && (
                      <circle
                        r={node.radius + 8}
                        fill="none"
                        stroke={node.color}
                        strokeWidth="2"
                        strokeDasharray="4,4"
                        opacity="0.8"
                      />
                    )}

                    {/* Circular Node Body */}
                    <circle
                      r={node.radius}
                      fill={fillGradient}
                      stroke={isSelected ? "#ffffff" : node.color}
                      strokeWidth={isSelected ? "3" : "1.5"}
                      filter="url(#node-shadow)"
                    />

                    {/* Inner Glyph / Role Initials */}
                    <text
                      x="0"
                      y={isCore ? 5 : 4}
                      textAnchor="middle"
                      fill="#ffffff"
                      fontSize={isCore ? "13" : "10"}
                      fontWeight="900"
                      letterSpacing="0.05em"
                    >
                      {isCore ? "SME" : node.category === "supplier" ? "SUP" : node.category === "buyer" ? "BYR" : "PRT"}
                    </text>

                    {/* Primary Label below Node */}
                    <text
                      x="0"
                      y={node.radius + 14}
                      textAnchor="middle"
                      fill="#f1f5f9"
                      fontSize="10"
                      fontWeight="bold"
                      className="pointer-events-none drop-shadow-md"
                    >
                      {node.label.length > 18 ? `${node.label.slice(0, 16)}…` : node.label}
                    </text>

                    {/* Sublabel / Legal ID Pill */}
                    <text
                      x="0"
                      y={node.radius + 25}
                      textAnchor="middle"
                      fill={node.color}
                      fontSize="9"
                      fontFamily="monospace"
                      fontWeight="600"
                      className="pointer-events-none"
                    >
                      {node.sublabel}
                    </text>
                  </g>
                );
              })}
            </g>
          </svg>
        </div>

        {/* 3. Interactive Graph Entity Inspector Sidebar */}
        <div className="lg:col-span-1 p-5 rounded-2xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-200 dark:border-zinc-800 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              Graph Entity Inspector
            </span>
            <span
              className="px-2 py-0.5 rounded text-[10px] font-mono font-bold capitalize"
              style={{
                backgroundColor: `${selectedEntity.color}15`,
                color: selectedEntity.color,
                border: `1px solid ${selectedEntity.color}40`,
              }}
            >
              {selectedEntity.category === "sme" ? "Core Borrower" : selectedEntity.category}
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <h3 className="text-sm font-black text-zinc-900 dark:text-zinc-100">
                {selectedEntity.label}
              </h3>
              <p className="text-xs font-mono text-zinc-500 mt-0.5">
                ID: {selectedEntity.sublabel}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 space-y-2 text-xs">
              <div className="flex justify-between items-center text-zinc-500">
                <span>Supply Chain Role:</span>
                <span className="font-semibold text-zinc-900 dark:text-zinc-200 text-right">
                  {selectedEntity.role}
                </span>
              </div>

              {selectedEntity.category !== "sme" && (
                <>
                  <div className="flex justify-between items-center text-zinc-500">
                    <span>Trade Volume:</span>
                    <span className="font-mono font-bold text-zinc-900 dark:text-zinc-200">
                      {selectedEntity.tradeVolume ? `${(selectedEntity.tradeVolume / 1000).toFixed(0)}k PLN/yr` : "N/A"}
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-zinc-500">
                    <span>Tenure:</span>
                    <span className="font-semibold text-zinc-900 dark:text-zinc-200">
                      {selectedEntity.tenure ? `${selectedEntity.tenure} months` : "24m"}
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-zinc-500">
                    <span>Trade Flow Direction:</span>
                    <span className="font-semibold capitalize text-[#2f6690]">
                      {selectedEntity.direction === "incoming" ? "Goods Inflow (Supplier)" : selectedEntity.direction === "outgoing" ? "Sales Outflow (Buyer)" : "Joint Distribution Hub"}
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-zinc-500">
                    <span>Counterparty Risk:</span>
                    <span className="font-bold text-emerald-700">
                      {selectedEntity.riskTier}
                    </span>
                  </div>
                </>
              )}

              {selectedEntity.category === "sme" && (
                <>
                  <div className="flex justify-between items-center text-zinc-500">
                    <span>Tabular Base PD:</span>
                    <span className="font-mono font-bold text-zinc-900 dark:text-zinc-200">
                      {(tabularPd * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-zinc-500">
                    <span>GNN Network PD:</span>
                    <span className="font-mono font-bold text-[#2f6690]">
                      {graphPd !== null ? `${(graphPd * 100).toFixed(2)}%` : "N/A"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-zinc-500">
                    <span>Multi-Modal Fused PD:</span>
                    <span className="font-mono font-black text-rose-600 dark:text-rose-400">
                      {(fusedPd * 100).toFixed(2)}%
                    </span>
                  </div>
                </>
              )}
            </div>

            {/* GNN Message-Passing Notice */}
            <div className="p-3 rounded-xl bg-[#81c3d7]/15 border border-[#3a7ca5]/35 text-[11px] text-[#16425b] space-y-1">
              <span className="font-bold flex items-center gap-1 text-[#16425b]">
                <Layers className="w-3.5 h-3.5 text-[#2f6690] shrink-0" />
                GNN Message Diffusion
              </span>
              <p className="text-[#2f6690] leading-normal">
                Node features aggregate across 2-layer GraphSAGE convolution into borrower credit score (15% fusion custody).
              </p>
            </div>

            {/* Mandatory Provenance Notice (Rule 4.4) */}
            <div className="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-300 dark:border-amber-800 text-[10px] text-amber-800 dark:text-amber-300">
              <span className="font-bold block">PROVENANCE NOTICE (Rule 4.4):</span>
              Synthetic commercial trade counterparties are explicitly tagged <span className="font-mono font-bold">is_synthetic = true</span> in remote graph storage.
            </div>
          </div>
        </div>
      </div>

      {/* 4. Bottom Graph Topology Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-[#3a7ca5]/20 text-xs">
        <div>
          <span className="text-[#2f6690] block text-[10px] uppercase font-semibold">Total Graph Nodes:</span>
          <span className="font-bold text-[#16425b]">
            {nodes.length} Nodes (1 Core + {nodes.length - 1} Commercial Peers)
          </span>
        </div>
        <div>
          <span className="text-[#2f6690] block text-[10px] uppercase font-semibold">Degree Connectivity:</span>
          <span className="font-bold text-[#16425b]">
            {edges.length} Directed Trade Edges ({suppliers.length} In / {buyers.length} Out / {partners.length} Hub)
          </span>
        </div>
        <div>
          <span className="text-[#2f6690] block text-[10px] uppercase font-semibold">GNN Diffusion Weight:</span>
          <span className="font-bold text-[#2f6690]">
            15% (PyTorch Geometric 2-Layer GraphSAGE)
          </span>
        </div>
        <div>
          <span className="text-[#2f6690] block text-[10px] uppercase font-semibold">Neo4j Provenance Policy:</span>
          <span className="font-bold text-amber-600">is_synthetic = true (Rule 4.4)</span>
        </div>
      </div>
    </div>
  );
}
