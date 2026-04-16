# def detect_risks(graph):
#     risks = []

#     for node in graph.nodes:
#         if graph.in_degree(node) > 3:
#             risks.append(f"{node} may be a bottleneck")

#         if graph.out_degree(node) == 0:
#             risks.append(f"{node} might be unused or isolated")

#     return risks


"""
Improved Risk Detection Agent
Features:
- Real SPOF (Single Point of Failure) detection
- Circular dependency detection
- Dead code detection
- Coupling analysis
- Criticality scoring
- LLM-based risk interpretation
"""

import logging
import networkx as nx
from typing import List, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class RiskDetector:
    """Comprehensive risk analysis for system architecture"""
    
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.risks = []
        self.warnings = []
    
    def detect_all_risks(self) -> Dict[str, Any]:
        """Run all risk detection algorithms"""
        return {
            "critical_risks": self._detect_spof(),
            "high_risks": self._detect_circular_dependencies(),
            "medium_risks": self._detect_high_coupling(),
            "code_quality": self._detect_dead_code(),
            "coupling_metrics": self._analyze_coupling(),
            "centrality_analysis": self._analyze_centrality(),
            "summary": self._generate_summary()
        }
    
    def _detect_spof(self) -> List[Dict[str, Any]]:
        """
        Detect Single Points of Failure (SPOF)
        
        SPOF criteria:
        - Node that if removed breaks connectivity
        - Critical service with no redundancy
        - Database connected to all services
        """
        spofs = []
        
        # Check for cut vertices (articulation points)
        try:
            # Only works on undirected graphs
            undirected = self.graph.to_undirected()
            articulation_points = list(nx.articulation_points(undirected))
            
            for node in articulation_points:
                in_degree = self.graph.in_degree(node)
                out_degree = self.graph.out_degree(node)
                
                # Check if it's a critical hub
                if in_degree > 3 or out_degree > 5:
                    spofs.append({
                        "node": node,
                        "type": "articulation_point",
                        "severity": "CRITICAL",
                        "description": f"'{node}' is a single point of failure. Removing it would disconnect the system.",
                        "in_degree": in_degree,
                        "out_degree": out_degree,
                        "affected_components": out_degree
                    })
        except Exception as e:
            logger.warning(f"Could not detect articulation points: {e}")
        
        # Detect hub nodes (high in-degree)
        for node in self.graph.nodes:
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            
            # Database or message broker pattern
            node_type = self.graph.nodes[node].get('type', '')
            is_service = node_type == 'service'
            
            if in_degree > 5 and out_degree == 0 and is_service:
                spofs.append({
                    "node": node,
                    "type": "database_hub",
                    "severity": "CRITICAL",
                    "description": f"'{node}' is accessed by {in_degree} components with no redundancy.",
                    "in_degree": in_degree,
                    "out_degree": out_degree,
                    "recommendation": "Add database replication or clustering"
                })
        
        return spofs
    
    def _detect_circular_dependencies(self) -> List[Dict[str, Any]]:
        """Detect circular dependencies and cycles in the system"""
        cycles = []
        
        try:
            # Find all cycles
            all_cycles = list(nx.simple_cycles(self.graph))
            
            for cycle in all_cycles[:10]:  # Limit to first 10
                cycle_str = " -> ".join(cycle) + f" -> {cycle[0]}"
                severity = "CRITICAL" if len(cycle) < 4 else "HIGH"
                
                cycles.append({
                    "nodes": cycle,
                    "severity": severity,
                    "description": f"Circular dependency detected: {cycle_str}",
                    "length": len(cycle),
                    "recommendation": "Refactor to break the cycle using dependency injection or redesign"
                })
        
        except Exception as e:
            logger.warning(f"Could not detect cycles: {e}")
        
        return cycles
    
    def _detect_high_coupling(self) -> List[Dict[str, Any]]:
        """Detect tightly coupled components"""
        coupling_risks = []
        
        # Find nodes with high inter-connectivity
        for node in self.graph.nodes:
            neighbors = set(self.graph.predecessors(node)) | set(self.graph.successors(node))
            
            # High coupling: connected to many other nodes
            if len(neighbors) > 8:
                coupling_risks.append({
                    "node": node,
                    "severity": "MEDIUM",
                    "description": f"'{node}' is tightly coupled to {len(neighbors)} other components.",
                    "coupled_count": len(neighbors),
                    "recommendation": "Consider splitting into smaller modules or using interfaces"
                })
        
        return coupling_risks
    
    def _detect_dead_code(self) -> List[Dict[str, Any]]:
        """Detect unused code modules"""
        dead_code = []
        
        for node in self.graph.nodes:
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            
            # Dead code: no incoming edges (not imported) and no outgoing edges
            if in_degree == 0 and out_degree == 0:
                node_type = self.graph.nodes[node].get('type', 'code')
                if node_type == 'code':
                    dead_code.append({
                        "node": node,
                        "severity": "LOW",
                        "description": f"'{node}' appears to be unused (no dependencies).",
                        "type": "isolated_module",
                        "recommendation": "Remove if not used, or verify it's intentionally isolated"
                    })
            
            # Leaf nodes (no dependencies on others)
            elif in_degree > 0 and out_degree == 0:
                dead_code.append({
                    "node": node,
                    "severity": "LOW",
                    "description": f"'{node}' is a leaf node with no downstream dependencies.",
                    "type": "leaf_module",
                    "incoming_deps": in_degree
                })
        
        return dead_code
    
    def _analyze_coupling(self) -> Dict[str, Any]:
        """Analyze coupling metrics"""
        metrics = {}
        
        # Average coupling
        total_edges = len(self.graph.edges)
        total_nodes = len(self.graph.nodes)
        
        if total_nodes > 0:
            avg_connections = total_edges / total_nodes
            metrics["average_connections_per_module"] = round(avg_connections, 2)
            metrics["coupling_ratio"] = round(total_edges / max(total_nodes - 1, 1), 2)
            metrics["density"] = round(
                2 * total_edges / (total_nodes * (total_nodes - 1)),
                2
            )
        
        return metrics
    
    def _analyze_centrality(self) -> Dict[str, Any]:
        """Analyze node centrality (importance)"""
        try:
            # Calculate different centrality measures
            degree_centrality = nx.degree_centrality(self.graph)
            betweenness = nx.betweenness_centrality(self.graph)
            closeness = nx.closeness_centrality(self.graph)
            
            # Find most important nodes
            top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:3]
            top_between = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                "most_connected": [{"node": node, "score": score} for node, score in top_degree],
                "key_bridges": [{"node": node, "score": score} for node, score in top_between],
                "total_centrality": sum(degree_centrality.values())
            }
        except Exception as e:
            logger.warning(f"Could not calculate centrality: {e}")
            return {}
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate overall health summary"""
        all_risks = (
            self._detect_spof() +
            self._detect_circular_dependencies() +
            self._detect_high_coupling() +
            self._detect_dead_code()
        )
        
        critical = [r for r in all_risks if r.get('severity') == 'CRITICAL']
        high = [r for r in all_risks if r.get('severity') == 'HIGH']
        medium = [r for r in all_risks if r.get('severity') == 'MEDIUM']
        
        # Health score (0-100)
        health_score = 100
        health_score -= len(critical) * 25
        health_score -= len(high) * 10
        health_score -= len(medium) * 5
        health_score = max(0, health_score)
        
        return {
            "total_risks": len(all_risks),
            "critical_count": len(critical),
            "high_count": len(high),
            "medium_count": len(medium),
            "health_score": health_score,
            "status": _get_health_status(health_score)
        }
    
    def get_risk_report(self) -> str:
        """Generate human-readable risk report"""
        all_risks = self.detect_all_risks()
        
        report = "=" * 60 + "\n"
        report += "ARCHITECTURE RISK ANALYSIS REPORT\n"
        report += "=" * 60 + "\n\n"
        
        # Summary
        summary = all_risks['summary']
        report += f"Health Score: {summary['health_score']}/100 ({summary['status']})\n"
        report += f"Total Risks Found: {summary['total_risks']}\n"
        report += f"  - Critical: {summary['critical_count']}\n"
        report += f"  - High: {summary['high_count']}\n"
        report += f"  - Medium: {summary['medium_count']}\n\n"
        
        # Critical risks
        if all_risks['critical_risks']:
            report += "CRITICAL RISKS:\n"
            for risk in all_risks['critical_risks']:
                report += f"  ⚠️  {risk['node']}: {risk['description']}\n"
                if 'recommendation' in risk:
                    report += f"      → {risk['recommendation']}\n"
            report += "\n"
        
        # Metrics
        report += "COUPLING METRICS:\n"
        metrics = all_risks['coupling_metrics']
        for key, value in metrics.items():
            report += f"  • {key}: {value}\n"
        
        return report

def _get_health_status(score: int) -> str:
    """Convert health score to status"""
    if score >= 80:
        return "EXCELLENT"
    elif score >= 60:
        return "GOOD"
    elif score >= 40:
        return "FAIR"
    elif score >= 20:
        return "POOR"
    else:
        return "CRITICAL"

def detect_risks(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Detect risks in architecture graph
    Returns comprehensive risk analysis
    """
    detector = RiskDetector(graph)
    return detector.detect_all_risks()

def get_risk_report(graph: nx.DiGraph) -> str:
    """Get human-readable risk report"""
    detector = RiskDetector(graph)
    return detector.get_risk_report()