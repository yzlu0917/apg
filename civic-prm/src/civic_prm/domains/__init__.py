from civic_prm.domains.algebra import sample_algebra_instance
from civic_prm.domains.blocksworld import sample_blocksworld_instance
from civic_prm.domains.graph_path import sample_graph_instance

DOMAIN_REGISTRY = {
    "algebra": sample_algebra_instance,
    "graph_path": sample_graph_instance,
    "blocksworld": sample_blocksworld_instance,
}

__all__ = ["DOMAIN_REGISTRY"]
