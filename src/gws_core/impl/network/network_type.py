from typing import Literal

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
    x: float | None
    y: float | None


class NetworkReactionDTO(BaseModelDTO):
    id: str
    name: str
    level: Literal[1, 2, 3]
    metabolites: dict[str, int]
    lower_bound: float | None
    upper_bound: float | None
    rhea_id: str | None
    enzymes: list[NetworkEnzymeDTO]
    data: dict | None
    layout: NetworkReactionLayoutDTO | None


class CompoundLayoutClusterDTO(BaseModelDTO):
    id: str
    name: str
    level: Literal[1, 2, 3]
    x: float | None
    y: float | None
    alt: str | None
    patwhay: str | None


class CompoundLayoutDTO(BaseModelDTO):
    clusters: dict[str, CompoundLayoutClusterDTO]


class NetworkMetaboliteDTO(BaseModelDTO):
    id: str
    name: str
    level: Literal[1, 2, 3]
    compartment: str | None
    charge: float | None
    mass: float | None
    formula: str | None
    chebi_id: str | None
    kegg_id: str | None
    layout: CompoundLayoutDTO | None
    type: Literal["default", "cofactor", "residue"]

    alt_chebi_ids: list | None
    monoisotopic_mass: float | None
    inchi: str | None
    inchikey: str | None


class NetworkDTO(BaseModelDTO):
    name: str | None
    metabolites: list[NetworkMetaboliteDTO]
    reactions: list[NetworkReactionDTO]
    compartments: list[NetworkCompartmentDTO]
