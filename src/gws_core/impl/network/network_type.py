from typing import Dict, List, Literal, Optional

from gws_core.core.model.model_dto import BaseModelDTO


class NetworkCompartmentDTO(BaseModelDTO):
    id: str
    go_id: str
    bigg_id: str
    name: str
    color: str


class NetworkEnzymeDTO(BaseModelDTO):
    name: str
    tax: dict
    ec_number: str
    pathways: dict
    related_deprecated_enzyme: dict


class NetworkReactionLayoutDTO(BaseModelDTO):
    x: Optional[float]
    y: Optional[float]


class NetworkReactionDTO(BaseModelDTO):
    id: str
    name: str
    level: Literal[1, 2, 3]
    metabolites: Dict[str, int]
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    rhea_id: Optional[str]
    enzymes: List[NetworkEnzymeDTO]
    data: Optional[dict]
    layout: Optional[NetworkReactionLayoutDTO]


class CompoundLayoutClusterDTO(BaseModelDTO):
    id: str
    name: str
    level: Literal[1, 2, 3]
    x: Optional[float]
    y: Optional[float]
    alt: Optional[str]
    patwhay: Optional[str]


class CompoundLayoutDTO(BaseModelDTO):
    clusters: Dict[str, CompoundLayoutClusterDTO]


class NetworkMetaboliteDTO(BaseModelDTO):
    id: str
    name: str
    level: Literal[1, 2, 3]
    compartment: Optional[str]
    charge: Optional[float]
    mass: Optional[float]
    formula: Optional[str]
    chebi_id: Optional[str]
    kegg_id: Optional[str]
    layout: Optional[CompoundLayoutDTO]
    type: Literal["default", "cofactor", "residue"]

    alt_chebi_ids: Optional[list]
    monoisotopic_mass: Optional[float]
    inchi: Optional[str]
    inchikey: Optional[str]


class NetworkDTO(BaseModelDTO):
    name: Optional[str]
    metabolites: List[NetworkMetaboliteDTO]
    reactions: List[NetworkReactionDTO]
    compartments: List[NetworkCompartmentDTO]
