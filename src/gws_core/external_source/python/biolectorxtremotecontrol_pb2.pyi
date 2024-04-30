from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WellLabel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    A01: _ClassVar[WellLabel]
    A02: _ClassVar[WellLabel]
    A03: _ClassVar[WellLabel]
    A04: _ClassVar[WellLabel]
    A05: _ClassVar[WellLabel]
    A06: _ClassVar[WellLabel]
    A07: _ClassVar[WellLabel]
    A08: _ClassVar[WellLabel]
    B01: _ClassVar[WellLabel]
    B02: _ClassVar[WellLabel]
    B03: _ClassVar[WellLabel]
    B04: _ClassVar[WellLabel]
    B05: _ClassVar[WellLabel]
    B06: _ClassVar[WellLabel]
    B07: _ClassVar[WellLabel]
    B08: _ClassVar[WellLabel]
    C01: _ClassVar[WellLabel]
    C02: _ClassVar[WellLabel]
    C03: _ClassVar[WellLabel]
    C04: _ClassVar[WellLabel]
    C05: _ClassVar[WellLabel]
    C06: _ClassVar[WellLabel]
    C07: _ClassVar[WellLabel]
    C08: _ClassVar[WellLabel]
    D01: _ClassVar[WellLabel]
    D02: _ClassVar[WellLabel]
    D03: _ClassVar[WellLabel]
    D04: _ClassVar[WellLabel]
    D05: _ClassVar[WellLabel]
    D06: _ClassVar[WellLabel]
    D07: _ClassVar[WellLabel]
    D08: _ClassVar[WellLabel]
    E01: _ClassVar[WellLabel]
    E02: _ClassVar[WellLabel]
    E03: _ClassVar[WellLabel]
    E04: _ClassVar[WellLabel]
    E05: _ClassVar[WellLabel]
    E06: _ClassVar[WellLabel]
    E07: _ClassVar[WellLabel]
    E08: _ClassVar[WellLabel]
    F01: _ClassVar[WellLabel]
    F02: _ClassVar[WellLabel]
    F03: _ClassVar[WellLabel]
    F04: _ClassVar[WellLabel]
    F05: _ClassVar[WellLabel]
    F06: _ClassVar[WellLabel]
    F07: _ClassVar[WellLabel]
    F08: _ClassVar[WellLabel]
    LABEL_UNKNOWN: _ClassVar[WellLabel]

class StdItemStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OK: _ClassVar[StdItemStatus]
    UNKNOWN_ERROR: _ClassVar[StdItemStatus]

class StopProtocolStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[StopProtocolStatus]
    SUCCESS: _ClassVar[StopProtocolStatus]
    NOT_RUNNING: _ClassVar[StopProtocolStatus]

class CoverStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    COV_UNKNOWN: _ClassVar[CoverStatus]
    COV_MOVING: _ClassVar[CoverStatus]
    COV_FAILING: _ClassVar[CoverStatus]
    COV_OPEN: _ClassVar[CoverStatus]
    COV_CLOSED: _ClassVar[CoverStatus]

class GassingMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    GMODE_UNKNOWN: _ClassVar[GassingMode]
    GMODE_OFF: _ClassVar[GassingMode]
    GMODE_AIR: _ClassVar[GassingMode]
    GMODE_ANAEROBE: _ClassVar[GassingMode]
    GMODE_GASSING_O2_UP: _ClassVar[GassingMode]
    GMODE_GASSING_O2_DOWN: _ClassVar[GassingMode]
    GMODE_GASSING_CO2_UP: _ClassVar[GassingMode]

class GasTypeN(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    GTT_UNKNOWN: _ClassVar[GasTypeN]
    GTT_O2: _ClassVar[GasTypeN]
    GTT_CO2: _ClassVar[GasTypeN]

class LAMModes(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LAM_PWM: _ClassVar[LAMModes]
    LAM_DC: _ClassVar[LAMModes]
    LAM_UNKNOWN: _ClassVar[LAMModes]

class CommentKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    C_UNKNOWN: _ClassVar[CommentKind]
    C_SERVICE: _ClassVar[CommentKind]
    C_USER: _ClassVar[CommentKind]
    C_SYSTEM: _ClassVar[CommentKind]
A01: WellLabel
A02: WellLabel
A03: WellLabel
A04: WellLabel
A05: WellLabel
A06: WellLabel
A07: WellLabel
A08: WellLabel
B01: WellLabel
B02: WellLabel
B03: WellLabel
B04: WellLabel
B05: WellLabel
B06: WellLabel
B07: WellLabel
B08: WellLabel
C01: WellLabel
C02: WellLabel
C03: WellLabel
C04: WellLabel
C05: WellLabel
C06: WellLabel
C07: WellLabel
C08: WellLabel
D01: WellLabel
D02: WellLabel
D03: WellLabel
D04: WellLabel
D05: WellLabel
D06: WellLabel
D07: WellLabel
D08: WellLabel
E01: WellLabel
E02: WellLabel
E03: WellLabel
E04: WellLabel
E05: WellLabel
E06: WellLabel
E07: WellLabel
E08: WellLabel
F01: WellLabel
F02: WellLabel
F03: WellLabel
F04: WellLabel
F05: WellLabel
F06: WellLabel
F07: WellLabel
F08: WellLabel
LABEL_UNKNOWN: WellLabel
OK: StdItemStatus
UNKNOWN_ERROR: StdItemStatus
UNKNOWN: StopProtocolStatus
SUCCESS: StopProtocolStatus
NOT_RUNNING: StopProtocolStatus
COV_UNKNOWN: CoverStatus
COV_MOVING: CoverStatus
COV_FAILING: CoverStatus
COV_OPEN: CoverStatus
COV_CLOSED: CoverStatus
GMODE_UNKNOWN: GassingMode
GMODE_OFF: GassingMode
GMODE_AIR: GassingMode
GMODE_ANAEROBE: GassingMode
GMODE_GASSING_O2_UP: GassingMode
GMODE_GASSING_O2_DOWN: GassingMode
GMODE_GASSING_CO2_UP: GassingMode
GTT_UNKNOWN: GasTypeN
GTT_O2: GasTypeN
GTT_CO2: GasTypeN
LAM_PWM: LAMModes
LAM_DC: LAMModes
LAM_UNKNOWN: LAMModes
C_UNKNOWN: CommentKind
C_SERVICE: CommentKind
C_USER: CommentKind
C_SYSTEM: CommentKind

class ProtocolInfo(_message.Message):
    __slots__ = ("protocol_id", "protocol_name")
    PROTOCOL_ID_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_NAME_FIELD_NUMBER: _ClassVar[int]
    protocol_id: str
    protocol_name: str
    def __init__(self, protocol_id: _Optional[str] = ..., protocol_name: _Optional[str] = ...) -> None: ...

class GetProtocolListResponse(_message.Message):
    __slots__ = ("protocols",)
    PROTOCOLS_FIELD_NUMBER: _ClassVar[int]
    protocols: _containers.RepeatedCompositeFieldContainer[ProtocolInfo]
    def __init__(self, protocols: _Optional[_Iterable[_Union[ProtocolInfo, _Mapping]]] = ...) -> None: ...

class MetaData(_message.Message):
    __slots__ = ("filename",)
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    filename: str
    def __init__(self, filename: _Optional[str] = ...) -> None: ...

class FileChunk(_message.Message):
    __slots__ = ("metadata", "chunk_data")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    CHUNK_DATA_FIELD_NUMBER: _ClassVar[int]
    metadata: MetaData
    chunk_data: bytes
    def __init__(self, metadata: _Optional[_Union[MetaData, _Mapping]] = ..., chunk_data: _Optional[bytes] = ...) -> None: ...

class StdResponse(_message.Message):
    __slots__ = ("status", "comment")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    status: StdItemStatus
    comment: str
    def __init__(self, status: _Optional[_Union[StdItemStatus, str]] = ..., comment: _Optional[str] = ...) -> None: ...

class StartProtocolResponse(_message.Message):
    __slots__ = ("status",)
    class StartProtocolReturnCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[StartProtocolResponse.StartProtocolReturnCode]
        SUCCESS: _ClassVar[StartProtocolResponse.StartProtocolReturnCode]
        PROTOCOL_NOT_FOUND: _ClassVar[StartProtocolResponse.StartProtocolReturnCode]
        DEVICE_NOT_IDLE: _ClassVar[StartProtocolResponse.StartProtocolReturnCode]
        LICENSE_MISSING: _ClassVar[StartProtocolResponse.StartProtocolReturnCode]
    UNKNOWN: StartProtocolResponse.StartProtocolReturnCode
    SUCCESS: StartProtocolResponse.StartProtocolReturnCode
    PROTOCOL_NOT_FOUND: StartProtocolResponse.StartProtocolReturnCode
    DEVICE_NOT_IDLE: StartProtocolResponse.StartProtocolReturnCode
    LICENSE_MISSING: StartProtocolResponse.StartProtocolReturnCode
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: StartProtocolResponse.StartProtocolReturnCode
    def __init__(self, status: _Optional[_Union[StartProtocolResponse.StartProtocolReturnCode, str]] = ...) -> None: ...

class StopProtocolResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: StopProtocolStatus
    def __init__(self, status: _Optional[_Union[StopProtocolStatus, str]] = ...) -> None: ...

class ContinueProtocolResponse(_message.Message):
    __slots__ = ("status",)
    class ContinueProtocolStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[ContinueProtocolResponse.ContinueProtocolStatus]
        SUCCESS: _ClassVar[ContinueProtocolResponse.ContinueProtocolStatus]
        NOT_PAUSED: _ClassVar[ContinueProtocolResponse.ContinueProtocolStatus]
    UNKNOWN: ContinueProtocolResponse.ContinueProtocolStatus
    SUCCESS: ContinueProtocolResponse.ContinueProtocolStatus
    NOT_PAUSED: ContinueProtocolResponse.ContinueProtocolStatus
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: ContinueProtocolResponse.ContinueProtocolStatus
    def __init__(self, status: _Optional[_Union[ContinueProtocolResponse.ContinueProtocolStatus, str]] = ...) -> None: ...

class ExperimentInfo(_message.Message):
    __slots__ = ("experiment_id", "protocol_id", "start_time", "file_path", "finished")
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_ID_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    FINISHED_FIELD_NUMBER: _ClassVar[int]
    experiment_id: str
    protocol_id: str
    start_time: str
    file_path: str
    finished: bool
    def __init__(self, experiment_id: _Optional[str] = ..., protocol_id: _Optional[str] = ..., start_time: _Optional[str] = ..., file_path: _Optional[str] = ..., finished: bool = ...) -> None: ...

class GetExperimentListResponse(_message.Message):
    __slots__ = ("experiment",)
    EXPERIMENT_FIELD_NUMBER: _ClassVar[int]
    experiment: _containers.RepeatedCompositeFieldContainer[ExperimentInfo]
    def __init__(self, experiment: _Optional[_Iterable[_Union[ExperimentInfo, _Mapping]]] = ...) -> None: ...

class UpdateRunningExperimentResponse(_message.Message):
    __slots__ = ("update_script_replies",)
    class UpdateScriptReply(_message.Message):
        __slots__ = ("id", "update_result", "message")
        class UpdateScriptResult(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            OK: _ClassVar[UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult]
            NO_SCRIPTS: _ClassVar[UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult]
            EMPTY_SCRIPT_ID: _ClassVar[UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult]
            DUPLICATE_SCRIPT_ID: _ClassVar[UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult]
            NULL_SCRIPT: _ClassVar[UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult]
            SYNTAX_ERROR: _ClassVar[UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult]
            DRY_RUN_ERROR: _ClassVar[UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult]
            UNSPECIFIED_ERROR: _ClassVar[UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult]
        OK: UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult
        NO_SCRIPTS: UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult
        EMPTY_SCRIPT_ID: UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult
        DUPLICATE_SCRIPT_ID: UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult
        NULL_SCRIPT: UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult
        SYNTAX_ERROR: UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult
        DRY_RUN_ERROR: UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult
        UNSPECIFIED_ERROR: UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult
        ID_FIELD_NUMBER: _ClassVar[int]
        UPDATE_RESULT_FIELD_NUMBER: _ClassVar[int]
        MESSAGE_FIELD_NUMBER: _ClassVar[int]
        id: str
        update_result: UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult
        message: str
        def __init__(self, id: _Optional[str] = ..., update_result: _Optional[_Union[UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult, str]] = ..., message: _Optional[str] = ...) -> None: ...
    UPDATE_SCRIPT_REPLIES_FIELD_NUMBER: _ClassVar[int]
    update_script_replies: _containers.RepeatedCompositeFieldContainer[UpdateRunningExperimentResponse.UpdateScriptReply]
    def __init__(self, update_script_replies: _Optional[_Iterable[_Union[UpdateRunningExperimentResponse.UpdateScriptReply, _Mapping]]] = ...) -> None: ...

class GetCurrentProgressResponse(_message.Message):
    __slots__ = ("cycle", "elapsed_time", "next_cycle_time", "current_channel", "total_channels", "current_cultivation", "total_cultivations")
    CYCLE_FIELD_NUMBER: _ClassVar[int]
    ELAPSED_TIME_FIELD_NUMBER: _ClassVar[int]
    NEXT_CYCLE_TIME_FIELD_NUMBER: _ClassVar[int]
    CURRENT_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_CULTIVATION_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CULTIVATIONS_FIELD_NUMBER: _ClassVar[int]
    cycle: int
    elapsed_time: int
    next_cycle_time: int
    current_channel: int
    total_channels: int
    current_cultivation: int
    total_cultivations: int
    def __init__(self, cycle: _Optional[int] = ..., elapsed_time: _Optional[int] = ..., next_cycle_time: _Optional[int] = ..., current_channel: _Optional[int] = ..., total_channels: _Optional[int] = ..., current_cultivation: _Optional[int] = ..., total_cultivations: _Optional[int] = ...) -> None: ...

class GetTemperatureControlStatusResponse(_message.Message):
    __slots__ = ("actual_temperature", "target_temperature", "enabled")
    ACTUAL_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    TARGET_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    actual_temperature: float
    target_temperature: float
    enabled: bool
    def __init__(self, actual_temperature: _Optional[float] = ..., target_temperature: _Optional[float] = ..., enabled: bool = ...) -> None: ...

class GetShakerControlStatusResponse(_message.Message):
    __slots__ = ("actual_rpm", "target_rpm", "enabled")
    ACTUAL_RPM_FIELD_NUMBER: _ClassVar[int]
    TARGET_RPM_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    actual_rpm: int
    target_rpm: int
    enabled: bool
    def __init__(self, actual_rpm: _Optional[int] = ..., target_rpm: _Optional[int] = ..., enabled: bool = ...) -> None: ...

class GetCoverStateResponse(_message.Message):
    __slots__ = ("cover_state",)
    COVER_STATE_FIELD_NUMBER: _ClassVar[int]
    cover_state: CoverStatus
    def __init__(self, cover_state: _Optional[_Union[CoverStatus, str]] = ...) -> None: ...

class GetActualGassingModeResponse(_message.Message):
    __slots__ = ("gassing_mode",)
    GASSING_MODE_FIELD_NUMBER: _ClassVar[int]
    gassing_mode: GassingMode
    def __init__(self, gassing_mode: _Optional[_Union[GassingMode, str]] = ...) -> None: ...

class GetGasPercentageRequest(_message.Message):
    __slots__ = ("gas_type",)
    GAS_TYPE_FIELD_NUMBER: _ClassVar[int]
    gas_type: GasTypeN
    def __init__(self, gas_type: _Optional[_Union[GasTypeN, str]] = ...) -> None: ...

class SetTargetGasPercentageRequest(_message.Message):
    __slots__ = ("gas_type", "gas_percentage")
    GAS_TYPE_FIELD_NUMBER: _ClassVar[int]
    GAS_PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    gas_type: GasTypeN
    gas_percentage: float
    def __init__(self, gas_type: _Optional[_Union[GasTypeN, str]] = ..., gas_percentage: _Optional[float] = ...) -> None: ...

class CultivationValuesItem(_message.Message):
    __slots__ = ("label", "current_volume", "pumped_volume_a", "pumped_volume_b", "pumped_external", "value")
    class Value(_message.Message):
        __slots__ = ("index", "name", "value", "time_stamp")
        INDEX_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        TIME_STAMP_FIELD_NUMBER: _ClassVar[int]
        index: int
        name: str
        value: float
        time_stamp: _timestamp_pb2.Timestamp
        def __init__(self, index: _Optional[int] = ..., name: _Optional[str] = ..., value: _Optional[float] = ..., time_stamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
    LABEL_FIELD_NUMBER: _ClassVar[int]
    CURRENT_VOLUME_FIELD_NUMBER: _ClassVar[int]
    PUMPED_VOLUME_A_FIELD_NUMBER: _ClassVar[int]
    PUMPED_VOLUME_B_FIELD_NUMBER: _ClassVar[int]
    PUMPED_EXTERNAL_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    label: WellLabel
    current_volume: float
    pumped_volume_a: float
    pumped_volume_b: float
    pumped_external: float
    value: _containers.RepeatedCompositeFieldContainer[CultivationValuesItem.Value]
    def __init__(self, label: _Optional[_Union[WellLabel, str]] = ..., current_volume: _Optional[float] = ..., pumped_volume_a: _Optional[float] = ..., pumped_volume_b: _Optional[float] = ..., pumped_external: _Optional[float] = ..., value: _Optional[_Iterable[_Union[CultivationValuesItem.Value, _Mapping]]] = ...) -> None: ...

class GetCultivationValuesResponse(_message.Message):
    __slots__ = ("cultivation",)
    CULTIVATION_FIELD_NUMBER: _ClassVar[int]
    cultivation: _containers.RepeatedCompositeFieldContainer[CultivationValuesItem]
    def __init__(self, cultivation: _Optional[_Iterable[_Union[CultivationValuesItem, _Mapping]]] = ...) -> None: ...

class PhControlParams(_message.Message):
    __slots__ = ("p", "i", "v_min", "v_max", "deadband", "start_volume")
    P_FIELD_NUMBER: _ClassVar[int]
    I_FIELD_NUMBER: _ClassVar[int]
    V_MIN_FIELD_NUMBER: _ClassVar[int]
    V_MAX_FIELD_NUMBER: _ClassVar[int]
    DEADBAND_FIELD_NUMBER: _ClassVar[int]
    START_VOLUME_FIELD_NUMBER: _ClassVar[int]
    p: float
    i: float
    v_min: float
    v_max: float
    deadband: float
    start_volume: float
    def __init__(self, p: _Optional[float] = ..., i: _Optional[float] = ..., v_min: _Optional[float] = ..., v_max: _Optional[float] = ..., deadband: _Optional[float] = ..., start_volume: _Optional[float] = ...) -> None: ...

class GetPhControlStatusResponse(_message.Message):
    __slots__ = ("control_status",)
    class ControlStatus(_message.Message):
        __slots__ = ("label", "target_ph", "current_ph", "params")
        LABEL_FIELD_NUMBER: _ClassVar[int]
        TARGET_PH_FIELD_NUMBER: _ClassVar[int]
        CURRENT_PH_FIELD_NUMBER: _ClassVar[int]
        PARAMS_FIELD_NUMBER: _ClassVar[int]
        label: WellLabel
        target_ph: float
        current_ph: float
        params: PhControlParams
        def __init__(self, label: _Optional[_Union[WellLabel, str]] = ..., target_ph: _Optional[float] = ..., current_ph: _Optional[float] = ..., params: _Optional[_Union[PhControlParams, _Mapping]] = ...) -> None: ...
    CONTROL_STATUS_FIELD_NUMBER: _ClassVar[int]
    control_status: _containers.RepeatedCompositeFieldContainer[GetPhControlStatusResponse.ControlStatus]
    def __init__(self, control_status: _Optional[_Iterable[_Union[GetPhControlStatusResponse.ControlStatus, _Mapping]]] = ...) -> None: ...

class SetTargetPhRequest(_message.Message):
    __slots__ = ("label", "ph")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    PH_FIELD_NUMBER: _ClassVar[int]
    label: WellLabel
    ph: float
    def __init__(self, label: _Optional[_Union[WellLabel, str]] = ..., ph: _Optional[float] = ...) -> None: ...

class SetPhControlStateRequest(_message.Message):
    __slots__ = ("label", "enabled")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    label: WellLabel
    enabled: bool
    def __init__(self, label: _Optional[_Union[WellLabel, str]] = ..., enabled: bool = ...) -> None: ...

class SetPhControlParamsRequest(_message.Message):
    __slots__ = ("label", "params")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    label: WellLabel
    params: PhControlParams
    def __init__(self, label: _Optional[_Union[WellLabel, str]] = ..., params: _Optional[_Union[PhControlParams, _Mapping]] = ...) -> None: ...

class FeedRequest(_message.Message):
    __slots__ = ("label", "source_label")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    SOURCE_LABEL_FIELD_NUMBER: _ClassVar[int]
    label: WellLabel
    source_label: str
    def __init__(self, label: _Optional[_Union[WellLabel, str]] = ..., source_label: _Optional[str] = ...) -> None: ...

class SetFeedControlParamsRequest(_message.Message):
    __slots__ = ("label", "source_label", "a", "b", "c", "d")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    SOURCE_LABEL_FIELD_NUMBER: _ClassVar[int]
    A_FIELD_NUMBER: _ClassVar[int]
    B_FIELD_NUMBER: _ClassVar[int]
    C_FIELD_NUMBER: _ClassVar[int]
    D_FIELD_NUMBER: _ClassVar[int]
    label: WellLabel
    source_label: str
    a: float
    b: float
    c: float
    d: float
    def __init__(self, label: _Optional[_Union[WellLabel, str]] = ..., source_label: _Optional[str] = ..., a: _Optional[float] = ..., b: _Optional[float] = ..., c: _Optional[float] = ..., d: _Optional[float] = ...) -> None: ...

class RunFeedPulseRequest(_message.Message):
    __slots__ = ("label", "source_label", "volume")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    SOURCE_LABEL_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    label: WellLabel
    source_label: str
    volume: float
    def __init__(self, label: _Optional[_Union[WellLabel, str]] = ..., source_label: _Optional[str] = ..., volume: _Optional[float] = ...) -> None: ...

class SetLAMWorkModeRequest(_message.Message):
    __slots__ = ("mode",)
    MODE_FIELD_NUMBER: _ClassVar[int]
    mode: LAMModes
    def __init__(self, mode: _Optional[_Union[LAMModes, str]] = ...) -> None: ...

class Power(_message.Message):
    __slots__ = ("index", "value")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    index: int
    value: float
    def __init__(self, index: _Optional[int] = ..., value: _Optional[float] = ...) -> None: ...

class SetLAMRelativePowersRequest(_message.Message):
    __slots__ = ("powers",)
    POWERS_FIELD_NUMBER: _ClassVar[int]
    powers: _containers.RepeatedCompositeFieldContainer[Power]
    def __init__(self, powers: _Optional[_Iterable[_Union[Power, _Mapping]]] = ...) -> None: ...

class GetLAMStatusResponse(_message.Message):
    __slots__ = ("frequency", "mode", "powers")
    FREQUENCY_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    POWERS_FIELD_NUMBER: _ClassVar[int]
    frequency: float
    mode: LAMModes
    powers: _containers.RepeatedCompositeFieldContainer[Power]
    def __init__(self, frequency: _Optional[float] = ..., mode: _Optional[_Union[LAMModes, str]] = ..., powers: _Optional[_Iterable[_Union[Power, _Mapping]]] = ...) -> None: ...

class ShakerStatus(_message.Message):
    __slots__ = ("actual_rpm", "target_rpm", "enabled")
    ACTUAL_RPM_FIELD_NUMBER: _ClassVar[int]
    TARGET_RPM_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    actual_rpm: float
    target_rpm: float
    enabled: float
    def __init__(self, actual_rpm: _Optional[float] = ..., target_rpm: _Optional[float] = ..., enabled: _Optional[float] = ...) -> None: ...

class TemperatureStatus(_message.Message):
    __slots__ = ("actual_temperature", "target_temperature", "enabled")
    ACTUAL_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    TARGET_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    actual_temperature: float
    target_temperature: float
    enabled: bool
    def __init__(self, actual_temperature: _Optional[float] = ..., target_temperature: _Optional[float] = ..., enabled: bool = ...) -> None: ...

class MeasurementStatus(_message.Message):
    __slots__ = ("cultivation", "channel_index", "channel_name", "value", "experiment_duration", "time_stamp")
    CULTIVATION_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_INDEX_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_DURATION_FIELD_NUMBER: _ClassVar[int]
    TIME_STAMP_FIELD_NUMBER: _ClassVar[int]
    cultivation: WellLabel
    channel_index: int
    channel_name: str
    value: float
    experiment_duration: int
    time_stamp: _timestamp_pb2.Timestamp
    def __init__(self, cultivation: _Optional[_Union[WellLabel, str]] = ..., channel_index: _Optional[int] = ..., channel_name: _Optional[str] = ..., value: _Optional[float] = ..., experiment_duration: _Optional[int] = ..., time_stamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class StatusComment(_message.Message):
    __slots__ = ("kind", "comment")
    KIND_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    kind: CommentKind
    comment: str
    def __init__(self, kind: _Optional[_Union[CommentKind, str]] = ..., comment: _Optional[str] = ...) -> None: ...

class StatusUpdateStreamResponse(_message.Message):
    __slots__ = ("cover_state", "actual_rpm", "target_rpm", "shaker_enabled", "actual_temperature", "target_temperature", "temperature_enabled", "comment_status", "measurement_status", "o2", "co2", "flow_rate")
    COVER_STATE_FIELD_NUMBER: _ClassVar[int]
    ACTUAL_RPM_FIELD_NUMBER: _ClassVar[int]
    TARGET_RPM_FIELD_NUMBER: _ClassVar[int]
    SHAKER_ENABLED_FIELD_NUMBER: _ClassVar[int]
    ACTUAL_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    TARGET_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_ENABLED_FIELD_NUMBER: _ClassVar[int]
    COMMENT_STATUS_FIELD_NUMBER: _ClassVar[int]
    MEASUREMENT_STATUS_FIELD_NUMBER: _ClassVar[int]
    O2_FIELD_NUMBER: _ClassVar[int]
    CO2_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    cover_state: CoverStatus
    actual_rpm: int
    target_rpm: int
    shaker_enabled: bool
    actual_temperature: float
    target_temperature: float
    temperature_enabled: bool
    comment_status: StatusComment
    measurement_status: MeasurementStatus
    o2: float
    co2: float
    flow_rate: float
    def __init__(self, cover_state: _Optional[_Union[CoverStatus, str]] = ..., actual_rpm: _Optional[int] = ..., target_rpm: _Optional[int] = ..., shaker_enabled: bool = ..., actual_temperature: _Optional[float] = ..., target_temperature: _Optional[float] = ..., temperature_enabled: bool = ..., comment_status: _Optional[_Union[StatusComment, _Mapping]] = ..., measurement_status: _Optional[_Union[MeasurementStatus, _Mapping]] = ..., o2: _Optional[float] = ..., co2: _Optional[float] = ..., flow_rate: _Optional[float] = ...) -> None: ...
