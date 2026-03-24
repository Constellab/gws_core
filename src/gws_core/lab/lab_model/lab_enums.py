from enum import Enum


class LabEnvironment(Enum):
    ON_CLOUD = "ON_CLOUD"
    DESKTOP = "DESKTOP"
    LOCAL = "LOCAL"


class LabMode(Enum):
    PROD = "prod"
    DEV = "dev"
