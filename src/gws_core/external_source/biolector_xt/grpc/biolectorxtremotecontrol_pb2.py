# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: biolectorxtremotecontrol.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1e\x62iolectorxtremotecontrol.proto\x12\x0f\x62iolectorxt.api\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x1fgoogle/protobuf/timestamp.proto\":\n\x0cProtocolInfo\x12\x13\n\x0bprotocol_id\x18\x01 \x01(\t\x12\x15\n\rprotocol_name\x18\x02 \x01(\t\"K\n\x17GetProtocolListResponse\x12\x30\n\tprotocols\x18\x01 \x03(\x0b\x32\x1d.biolectorxt.api.ProtocolInfo\"\x1c\n\x08MetaData\x12\x10\n\x08\x66ilename\x18\x01 \x01(\t\"[\n\tFileChunk\x12-\n\x08metadata\x18\x01 \x01(\x0b\x32\x19.biolectorxt.api.MetaDataH\x00\x12\x14\n\nchunk_data\x18\x02 \x01(\x0cH\x00\x42\t\n\x07request\"N\n\x0bStdResponse\x12.\n\x06status\x18\x01 \x01(\x0e\x32\x1e.biolectorxt.api.StdItemStatus\x12\x0f\n\x07\x63omment\x18\x02 \x01(\t\"\xde\x01\n\x15StartProtocolResponse\x12N\n\x06status\x18\x01 \x01(\x0e\x32>.biolectorxt.api.StartProtocolResponse.StartProtocolReturnCode\"u\n\x17StartProtocolReturnCode\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x0b\n\x07SUCCESS\x10\x01\x12\x16\n\x12PROTOCOL_NOT_FOUND\x10\x02\x12\x13\n\x0f\x44\x45VICE_NOT_IDLE\x10\x03\x12\x13\n\x0fLICENSE_MISSING\x10\x04\"K\n\x14StopProtocolResponse\x12\x33\n\x06status\x18\x01 \x01(\x0e\x32#.biolectorxt.api.StopProtocolStatus\"\xb0\x01\n\x18\x43ontinueProtocolResponse\x12P\n\x06status\x18\x01 \x01(\x0e\x32@.biolectorxt.api.ContinueProtocolResponse.ContinueProtocolStatus\"B\n\x16\x43ontinueProtocolStatus\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x0b\n\x07SUCCESS\x10\x01\x12\x0e\n\nNOT_PAUSED\x10\x02\"u\n\x0e\x45xperimentInfo\x12\x15\n\rexperiment_id\x18\x01 \x01(\t\x12\x13\n\x0bprotocol_id\x18\x02 \x01(\t\x12\x12\n\nstart_time\x18\x03 \x01(\t\x12\x11\n\tfile_path\x18\x04 \x01(\t\x12\x10\n\x08\x66inished\x18\x05 \x01(\x08\"P\n\x19GetExperimentListResponse\x12\x33\n\nexperiment\x18\x01 \x03(\x0b\x32\x1f.biolectorxt.api.ExperimentInfo\"\xcf\x03\n\x1fUpdateRunningExperimentResponse\x12\x61\n\x15update_script_replies\x18\x03 \x03(\x0b\x32\x42.biolectorxt.api.UpdateRunningExperimentResponse.UpdateScriptReply\x1a\xc8\x02\n\x11UpdateScriptReply\x12\n\n\x02id\x18\x01 \x01(\t\x12l\n\rupdate_result\x18\x02 \x01(\x0e\x32U.biolectorxt.api.UpdateRunningExperimentResponse.UpdateScriptReply.UpdateScriptResult\x12\x0f\n\x07message\x18\x03 \x01(\t\"\xa7\x01\n\x12UpdateScriptResult\x12\x06\n\x02OK\x10\x00\x12\x0e\n\nNO_SCRIPTS\x10\x02\x12\x13\n\x0f\x45MPTY_SCRIPT_ID\x10\x03\x12\x17\n\x13\x44UPLICATE_SCRIPT_ID\x10\x04\x12\x0f\n\x0bNULL_SCRIPT\x10\x05\x12\x10\n\x0cSYNTAX_ERROR\x10\x06\x12\x11\n\rDRY_RUN_ERROR\x10\x07\x12\x15\n\x11UNSPECIFIED_ERROR\x10\x08\"\xc4\x01\n\x1aGetCurrentProgressResponse\x12\r\n\x05\x63ycle\x18\x01 \x01(\x04\x12\x14\n\x0c\x65lapsed_time\x18\x02 \x01(\x04\x12\x17\n\x0fnext_cycle_time\x18\x03 \x01(\x04\x12\x17\n\x0f\x63urrent_channel\x18\x04 \x01(\r\x12\x16\n\x0etotal_channels\x18\x05 \x01(\r\x12\x1b\n\x13\x63urrent_cultivation\x18\x06 \x01(\r\x12\x1a\n\x12total_cultivations\x18\x07 \x01(\r\"n\n#GetTemperatureControlStatusResponse\x12\x1a\n\x12\x61\x63tual_temperature\x18\x01 \x01(\x02\x12\x1a\n\x12target_temperature\x18\x02 \x01(\x02\x12\x0f\n\x07\x65nabled\x18\x03 \x01(\x08\"Y\n\x1eGetShakerControlStatusResponse\x12\x12\n\nactual_rpm\x18\x01 \x01(\r\x12\x12\n\ntarget_rpm\x18\x02 \x01(\r\x12\x0f\n\x07\x65nabled\x18\x03 \x01(\x08\"J\n\x15GetCoverStateResponse\x12\x31\n\x0b\x63over_state\x18\x01 \x01(\x0e\x32\x1c.biolectorxt.api.CoverStatus\"R\n\x1cGetActualGassingModeResponse\x12\x32\n\x0cgassing_mode\x18\x01 \x01(\x0e\x32\x1c.biolectorxt.api.GassingMode\"F\n\x17GetGasPercentageRequest\x12+\n\x08gas_type\x18\x01 \x01(\x0e\x32\x19.biolectorxt.api.GasTypeN\"d\n\x1dSetTargetGasPercentageRequest\x12+\n\x08gas_type\x18\x01 \x01(\x0e\x32\x19.biolectorxt.api.GasTypeN\x12\x16\n\x0egas_percentage\x18\x02 \x01(\x02\"\xc7\x02\n\x15\x43ultivationValuesItem\x12)\n\x05label\x18\x01 \x01(\x0e\x32\x1a.biolectorxt.api.WellLabel\x12\x16\n\x0e\x63urrent_volume\x18\x02 \x01(\x02\x12\x17\n\x0fpumped_volume_a\x18\x03 \x01(\x02\x12\x17\n\x0fpumped_volume_b\x18\x04 \x01(\x02\x12\x17\n\x0fpumped_external\x18\x05 \x01(\x02\x12;\n\x05value\x18\x06 \x03(\x0b\x32,.biolectorxt.api.CultivationValuesItem.Value\x1a\x63\n\x05Value\x12\r\n\x05index\x18\x01 \x01(\r\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\r\n\x05value\x18\x03 \x01(\x02\x12.\n\ntime_stamp\x18\x04 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\"[\n\x1cGetCultivationValuesResponse\x12;\n\x0b\x63ultivation\x18\x01 \x03(\x0b\x32&.biolectorxt.api.CultivationValuesItem\"m\n\x0fPhControlParams\x12\t\n\x01p\x18\x01 \x01(\x02\x12\t\n\x01i\x18\x02 \x01(\x02\x12\r\n\x05v_min\x18\x03 \x01(\x02\x12\r\n\x05v_max\x18\x04 \x01(\x02\x12\x10\n\x08\x64\x65\x61\x64\x62\x61nd\x18\x05 \x01(\x02\x12\x14\n\x0cstart_volume\x18\x06 \x01(\x02\"\x85\x02\n\x1aGetPhControlStatusResponse\x12Q\n\x0e\x63ontrol_status\x18\x01 \x03(\x0b\x32\x39.biolectorxt.api.GetPhControlStatusResponse.ControlStatus\x1a\x93\x01\n\rControlStatus\x12)\n\x05label\x18\x01 \x01(\x0e\x32\x1a.biolectorxt.api.WellLabel\x12\x11\n\ttarget_ph\x18\x02 \x01(\x02\x12\x12\n\ncurrent_ph\x18\x03 \x01(\x02\x12\x30\n\x06params\x18\x04 \x01(\x0b\x32 .biolectorxt.api.PhControlParams\"K\n\x12SetTargetPhRequest\x12)\n\x05label\x18\x01 \x01(\x0e\x32\x1a.biolectorxt.api.WellLabel\x12\n\n\x02ph\x18\x02 \x01(\x02\"V\n\x18SetPhControlStateRequest\x12)\n\x05label\x18\x01 \x01(\x0e\x32\x1a.biolectorxt.api.WellLabel\x12\x0f\n\x07\x65nabled\x18\x02 \x01(\x08\"x\n\x19SetPhControlParamsRequest\x12)\n\x05label\x18\x01 \x01(\x0e\x32\x1a.biolectorxt.api.WellLabel\x12\x30\n\x06params\x18\x02 \x01(\x0b\x32 .biolectorxt.api.PhControlParams\"N\n\x0b\x46\x65\x65\x64Request\x12)\n\x05label\x18\x01 \x01(\x0e\x32\x1a.biolectorxt.api.WellLabel\x12\x14\n\x0csource_label\x18\x02 \x01(\t\"\x8a\x01\n\x1bSetFeedControlParamsRequest\x12)\n\x05label\x18\x01 \x01(\x0e\x32\x1a.biolectorxt.api.WellLabel\x12\x14\n\x0csource_label\x18\x02 \x01(\t\x12\t\n\x01\x61\x18\x03 \x01(\x02\x12\t\n\x01\x62\x18\x04 \x01(\x02\x12\t\n\x01\x63\x18\x05 \x01(\x02\x12\t\n\x01\x64\x18\x06 \x01(\x02\"f\n\x13RunFeedPulseRequest\x12)\n\x05label\x18\x01 \x01(\x0e\x32\x1a.biolectorxt.api.WellLabel\x12\x14\n\x0csource_label\x18\x02 \x01(\t\x12\x0e\n\x06volume\x18\x03 \x01(\x02\"@\n\x15SetLAMWorkModeRequest\x12\'\n\x04mode\x18\x01 \x01(\x0e\x32\x19.biolectorxt.api.LAMModes\"%\n\x05Power\x12\r\n\x05index\x18\x01 \x01(\r\x12\r\n\x05value\x18\x02 \x01(\x02\"E\n\x1bSetLAMRelativePowersRequest\x12&\n\x06powers\x18\x01 \x03(\x0b\x32\x16.biolectorxt.api.Power\"z\n\x14GetLAMStatusResponse\x12\x11\n\tfrequency\x18\x01 \x01(\x02\x12\'\n\x04mode\x18\x02 \x01(\x0e\x32\x19.biolectorxt.api.LAMModes\x12&\n\x06powers\x18\x03 \x03(\x0b\x32\x16.biolectorxt.api.Power\"G\n\x0cShakerStatus\x12\x12\n\nactual_rpm\x18\x01 \x01(\x02\x12\x12\n\ntarget_rpm\x18\x02 \x01(\x02\x12\x0f\n\x07\x65nabled\x18\x03 \x01(\x02\"\\\n\x11TemperatureStatus\x12\x1a\n\x12\x61\x63tual_temperature\x18\x01 \x01(\x02\x12\x1a\n\x12target_temperature\x18\x02 \x01(\x02\x12\x0f\n\x07\x65nabled\x18\x03 \x01(\x08\"\xcd\x01\n\x11MeasurementStatus\x12/\n\x0b\x63ultivation\x18\x01 \x01(\x0e\x32\x1a.biolectorxt.api.WellLabel\x12\x15\n\rchannel_index\x18\x02 \x01(\r\x12\x14\n\x0c\x63hannel_name\x18\x03 \x01(\t\x12\r\n\x05value\x18\x04 \x01(\x02\x12\x1b\n\x13\x65xperiment_duration\x18\x05 \x01(\x04\x12.\n\ntime_stamp\x18\x06 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\"L\n\rStatusComment\x12*\n\x04kind\x18\x01 \x01(\x0e\x32\x1c.biolectorxt.api.CommentKind\x12\x0f\n\x07\x63omment\x18\x02 \x01(\t\"\xb2\x03\n\x1aStatusUpdateStreamResponse\x12\x33\n\x0b\x63over_state\x18\x01 \x01(\x0e\x32\x1c.biolectorxt.api.CoverStatusH\x00\x12\x14\n\nactual_rpm\x18\x02 \x01(\x05H\x00\x12\x14\n\ntarget_rpm\x18\x03 \x01(\x05H\x00\x12\x18\n\x0eshaker_enabled\x18\x04 \x01(\x08H\x00\x12\x1c\n\x12\x61\x63tual_temperature\x18\x05 \x01(\x02H\x00\x12\x1c\n\x12target_temperature\x18\x06 \x01(\x02H\x00\x12\x1d\n\x13temperature_enabled\x18\x07 \x01(\x08H\x00\x12\x38\n\x0e\x63omment_status\x18\x08 \x01(\x0b\x32\x1e.biolectorxt.api.StatusCommentH\x00\x12@\n\x12measurement_status\x18\t \x01(\x0b\x32\".biolectorxt.api.MeasurementStatusH\x00\x12\x0c\n\x02o2\x18\n \x01(\x02H\x00\x12\r\n\x03\x63o2\x18\x0b \x01(\x02H\x00\x12\x13\n\tflow_rate\x18\x0c \x01(\x02H\x00\x42\x10\n\x0e\x63urrent_status*\xce\x03\n\tWellLabel\x12\x07\n\x03\x41\x30\x31\x10\x00\x12\x07\n\x03\x41\x30\x32\x10\x01\x12\x07\n\x03\x41\x30\x33\x10\x02\x12\x07\n\x03\x41\x30\x34\x10\x03\x12\x07\n\x03\x41\x30\x35\x10\x04\x12\x07\n\x03\x41\x30\x36\x10\x05\x12\x07\n\x03\x41\x30\x37\x10\x06\x12\x07\n\x03\x41\x30\x38\x10\x07\x12\x07\n\x03\x42\x30\x31\x10\x08\x12\x07\n\x03\x42\x30\x32\x10\t\x12\x07\n\x03\x42\x30\x33\x10\n\x12\x07\n\x03\x42\x30\x34\x10\x0b\x12\x07\n\x03\x42\x30\x35\x10\x0c\x12\x07\n\x03\x42\x30\x36\x10\r\x12\x07\n\x03\x42\x30\x37\x10\x0e\x12\x07\n\x03\x42\x30\x38\x10\x0f\x12\x07\n\x03\x43\x30\x31\x10\x10\x12\x07\n\x03\x43\x30\x32\x10\x11\x12\x07\n\x03\x43\x30\x33\x10\x12\x12\x07\n\x03\x43\x30\x34\x10\x13\x12\x07\n\x03\x43\x30\x35\x10\x14\x12\x07\n\x03\x43\x30\x36\x10\x15\x12\x07\n\x03\x43\x30\x37\x10\x16\x12\x07\n\x03\x43\x30\x38\x10\x17\x12\x07\n\x03\x44\x30\x31\x10\x18\x12\x07\n\x03\x44\x30\x32\x10\x19\x12\x07\n\x03\x44\x30\x33\x10\x1a\x12\x07\n\x03\x44\x30\x34\x10\x1b\x12\x07\n\x03\x44\x30\x35\x10\x1c\x12\x07\n\x03\x44\x30\x36\x10\x1d\x12\x07\n\x03\x44\x30\x37\x10\x1e\x12\x07\n\x03\x44\x30\x38\x10\x1f\x12\x07\n\x03\x45\x30\x31\x10 \x12\x07\n\x03\x45\x30\x32\x10!\x12\x07\n\x03\x45\x30\x33\x10\"\x12\x07\n\x03\x45\x30\x34\x10#\x12\x07\n\x03\x45\x30\x35\x10$\x12\x07\n\x03\x45\x30\x36\x10%\x12\x07\n\x03\x45\x30\x37\x10&\x12\x07\n\x03\x45\x30\x38\x10\'\x12\x07\n\x03\x46\x30\x31\x10(\x12\x07\n\x03\x46\x30\x32\x10)\x12\x07\n\x03\x46\x30\x33\x10*\x12\x07\n\x03\x46\x30\x34\x10+\x12\x07\n\x03\x46\x30\x35\x10,\x12\x07\n\x03\x46\x30\x36\x10-\x12\x07\n\x03\x46\x30\x37\x10.\x12\x07\n\x03\x46\x30\x38\x10/\x12\x11\n\rLABEL_UNKNOWN\x10\x30**\n\rStdItemStatus\x12\x06\n\x02OK\x10\x00\x12\x11\n\rUNKNOWN_ERROR\x10\x01*?\n\x12StopProtocolStatus\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x0b\n\x07SUCCESS\x10\x01\x12\x0f\n\x0bNOT_RUNNING\x10\x02*]\n\x0b\x43overStatus\x12\x0f\n\x0b\x43OV_UNKNOWN\x10\x00\x12\x0e\n\nCOV_MOVING\x10\x01\x12\x0f\n\x0b\x43OV_FAILING\x10\x02\x12\x0c\n\x08\x43OV_OPEN\x10\x03\x12\x0e\n\nCOV_CLOSED\x10\x04*\xa0\x01\n\x0bGassingMode\x12\x11\n\rGMODE_UNKNOWN\x10\x00\x12\r\n\tGMODE_OFF\x10\x01\x12\r\n\tGMODE_AIR\x10\x02\x12\x12\n\x0eGMODE_ANAEROBE\x10\x03\x12\x17\n\x13GMODE_GASSING_O2_UP\x10\x04\x12\x19\n\x15GMODE_GASSING_O2_DOWN\x10\x05\x12\x18\n\x14GMODE_GASSING_CO2_UP\x10\x06*4\n\x08GasTypeN\x12\x0f\n\x0bGTT_UNKNOWN\x10\x00\x12\n\n\x06GTT_O2\x10\x01\x12\x0b\n\x07GTT_CO2\x10\x02*4\n\x08LAMModes\x12\x0b\n\x07LAM_PWM\x10\x00\x12\n\n\x06LAM_DC\x10\x01\x12\x0f\n\x0bLAM_UNKNOWN\x10\x02*E\n\x0b\x43ommentKind\x12\r\n\tC_UNKNOWN\x10\x00\x12\r\n\tC_SERVICE\x10\x01\x12\n\n\x06\x43_USER\x10\x02\x12\x0c\n\x08\x43_SYSTEM\x10\x03\x32\x8d\x1e\n\x18\x42ioLectorXtRemoteControl\x12R\n\x0cGetProtocols\x12\x16.google.protobuf.Empty\x1a(.biolectorxt.api.GetProtocolListResponse\"\x00\x12N\n\x0eUploadProtocol\x12\x1a.biolectorxt.api.FileChunk\x1a\x1c.biolectorxt.api.StdResponse\"\x00(\x01\x12P\n\x10\x44ownloadProtocol\x12\x1c.google.protobuf.StringValue\x1a\x1a.biolectorxt.api.FileChunk\"\x00\x30\x01\x12N\n\x0e\x44\x65leteProtocol\x12\x1c.google.protobuf.StringValue\x1a\x1c.biolectorxt.api.StdResponse\"\x00\x12Y\n\x11GetExperimentList\x12\x16.google.protobuf.Empty\x1a*.biolectorxt.api.GetExperimentListResponse\"\x00\x12R\n\x12\x44ownloadExperiment\x12\x1c.google.protobuf.StringValue\x1a\x1a.biolectorxt.api.FileChunk\"\x00\x30\x01\x12P\n\x10\x44\x65leteExperiment\x12\x1c.google.protobuf.StringValue\x1a\x1c.biolectorxt.api.StdResponse\"\x00\x12h\n\x14UpdateLiveExperiment\x12\x1c.google.protobuf.StringValue\x1a\x30.biolectorxt.api.UpdateRunningExperimentResponse\"\x00\x12W\n\rStartProtocol\x12\x1c.google.protobuf.StringValue\x1a&.biolectorxt.api.StartProtocolResponse\"\x00\x12O\n\x0cStopProtocol\x12\x16.google.protobuf.Empty\x1a%.biolectorxt.api.StopProtocolResponse\"\x00\x12\x45\n\rPauseProtocol\x12\x1a.google.protobuf.BoolValue\x1a\x16.google.protobuf.Empty\"\x00\x12W\n\x10\x43ontinueProtocol\x12\x16.google.protobuf.Empty\x1a).biolectorxt.api.ContinueProtocolResponse\"\x00\x12[\n\x12GetCurrentProgress\x12\x16.google.protobuf.Empty\x1a+.biolectorxt.api.GetCurrentProgressResponse\"\x00\x12m\n\x1bGetTemperatureControlStatus\x12\x16.google.protobuf.Empty\x1a\x34.biolectorxt.api.GetTemperatureControlStatusResponse\"\x00\x12O\n\x16SetTemperatureSetpoint\x12\x1b.google.protobuf.FloatValue\x1a\x16.google.protobuf.Empty\"\x00\x12T\n\x1cSetTemperatureControlEnabled\x12\x1a.google.protobuf.BoolValue\x1a\x16.google.protobuf.Empty\"\x00\x12\x63\n\x16GetShakerControlStatus\x12\x16.google.protobuf.Empty\x1a/.biolectorxt.api.GetShakerControlStatusResponse\"\x00\x12K\n\x11SetShakerSetpoint\x12\x1c.google.protobuf.UInt32Value\x1a\x16.google.protobuf.Empty\"\x00\x12H\n\x10SetShakerEnabled\x12\x1a.google.protobuf.BoolValue\x1a\x16.google.protobuf.Empty\"\x00\x12=\n\tOpenCover\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x12>\n\nCloseCover\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x12Q\n\rGetCoverState\x12\x16.google.protobuf.Empty\x1a&.biolectorxt.api.GetCoverStateResponse\"\x00\x12_\n\x14GetActualGassingMode\x12\x16.google.protobuf.Empty\x1a-.biolectorxt.api.GetActualGassingModeResponse\"\x00\x12K\n\x12GetGassingFlowrate\x12\x16.google.protobuf.Empty\x1a\x1b.google.protobuf.FloatValue\"\x00\x12K\n\x12SetGassingFlowrate\x12\x1b.google.protobuf.FloatValue\x1a\x16.google.protobuf.Empty\"\x00\x12\x61\n\x16GetTargetGasPercentage\x12(.biolectorxt.api.GetGasPercentageRequest\x1a\x1b.google.protobuf.FloatValue\"\x00\x12\x61\n\x16GetActualGasPercentage\x12(.biolectorxt.api.GetGasPercentageRequest\x1a\x1b.google.protobuf.FloatValue\"\x00\x12\x63\n\x17SetTargetGassPercentage\x12..biolectorxt.api.SetTargetGasPercentageRequest\x1a\x16.google.protobuf.Empty\"\x00\x12O\n\x17GetHumidityControlState\x12\x16.google.protobuf.Empty\x1a\x1a.google.protobuf.BoolValue\"\x00\x12O\n\x17SetHumidityControlState\x12\x1a.google.protobuf.BoolValue\x1a\x16.google.protobuf.Empty\"\x00\x12_\n\x14GetCultivationValues\x12\x16.google.protobuf.Empty\x1a-.biolectorxt.api.GetCultivationValuesResponse\"\x00\x12[\n\x12GetPhControlStatus\x12\x16.google.protobuf.Empty\x1a+.biolectorxt.api.GetPhControlStatusResponse\"\x00\x12L\n\x0bSetTargetPh\x12#.biolectorxt.api.SetTargetPhRequest\x1a\x16.google.protobuf.Empty\"\x00\x12X\n\x11SetPhControlState\x12).biolectorxt.api.SetPhControlStateRequest\x1a\x16.google.protobuf.Empty\"\x00\x12Z\n\x12SetPhControlParams\x12*.biolectorxt.api.SetPhControlParamsRequest\x1a\x16.google.protobuf.Empty\"\x00\x12\x43\n\tStartFeed\x12\x1c.biolectorxt.api.FeedRequest\x1a\x16.google.protobuf.Empty\"\x00\x12\x42\n\x08StopFeed\x12\x1c.biolectorxt.api.FeedRequest\x1a\x16.google.protobuf.Empty\"\x00\x12^\n\x14SetFeedControlParams\x12,.biolectorxt.api.SetFeedControlParamsRequest\x1a\x16.google.protobuf.Empty\"\x00\x12N\n\x0cRunFeedPulse\x12$.biolectorxt.api.RunFeedPulseRequest\x1a\x16.google.protobuf.Empty\"\x00\x12\x44\n\nAddComment\x12\x1c.google.protobuf.StringValue\x1a\x16.google.protobuf.Empty\"\x00\x12R\n\x0eSetLAMWorkMode\x12&.biolectorxt.api.SetLAMWorkModeRequest\x1a\x16.google.protobuf.Empty\"\x00\x12H\n\x0fSetLAMFrequency\x12\x1b.google.protobuf.FloatValue\x1a\x16.google.protobuf.Empty\"\x00\x12^\n\x14SetLAMRelativePowers\x12,.biolectorxt.api.SetLAMRelativePowersRequest\x1a\x16.google.protobuf.Empty\"\x00\x12O\n\x0cGetLAMStatus\x12\x16.google.protobuf.Empty\x1a%.biolectorxt.api.GetLAMStatusResponse\"\x00\x12]\n\x12StatusUpdateStream\x12\x16.google.protobuf.Empty\x1a+.biolectorxt.api.StatusUpdateStreamResponse\"\x00\x30\x01\x42\x06\xa2\x02\x03HLWb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'biolectorxtremotecontrol_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  _globals['DESCRIPTOR']._options = None
  _globals['DESCRIPTOR']._serialized_options = b'\242\002\003HLW'
  _globals['_WELLLABEL']._serialized_start=4970
  _globals['_WELLLABEL']._serialized_end=5432
  _globals['_STDITEMSTATUS']._serialized_start=5434
  _globals['_STDITEMSTATUS']._serialized_end=5476
  _globals['_STOPPROTOCOLSTATUS']._serialized_start=5478
  _globals['_STOPPROTOCOLSTATUS']._serialized_end=5541
  _globals['_COVERSTATUS']._serialized_start=5543
  _globals['_COVERSTATUS']._serialized_end=5636
  _globals['_GASSINGMODE']._serialized_start=5639
  _globals['_GASSINGMODE']._serialized_end=5799
  _globals['_GASTYPEN']._serialized_start=5801
  _globals['_GASTYPEN']._serialized_end=5853
  _globals['_LAMMODES']._serialized_start=5855
  _globals['_LAMMODES']._serialized_end=5907
  _globals['_COMMENTKIND']._serialized_start=5909
  _globals['_COMMENTKIND']._serialized_end=5978
  _globals['_PROTOCOLINFO']._serialized_start=145
  _globals['_PROTOCOLINFO']._serialized_end=203
  _globals['_GETPROTOCOLLISTRESPONSE']._serialized_start=205
  _globals['_GETPROTOCOLLISTRESPONSE']._serialized_end=280
  _globals['_METADATA']._serialized_start=282
  _globals['_METADATA']._serialized_end=310
  _globals['_FILECHUNK']._serialized_start=312
  _globals['_FILECHUNK']._serialized_end=403
  _globals['_STDRESPONSE']._serialized_start=405
  _globals['_STDRESPONSE']._serialized_end=483
  _globals['_STARTPROTOCOLRESPONSE']._serialized_start=486
  _globals['_STARTPROTOCOLRESPONSE']._serialized_end=708
  _globals['_STARTPROTOCOLRESPONSE_STARTPROTOCOLRETURNCODE']._serialized_start=591
  _globals['_STARTPROTOCOLRESPONSE_STARTPROTOCOLRETURNCODE']._serialized_end=708
  _globals['_STOPPROTOCOLRESPONSE']._serialized_start=710
  _globals['_STOPPROTOCOLRESPONSE']._serialized_end=785
  _globals['_CONTINUEPROTOCOLRESPONSE']._serialized_start=788
  _globals['_CONTINUEPROTOCOLRESPONSE']._serialized_end=964
  _globals['_CONTINUEPROTOCOLRESPONSE_CONTINUEPROTOCOLSTATUS']._serialized_start=898
  _globals['_CONTINUEPROTOCOLRESPONSE_CONTINUEPROTOCOLSTATUS']._serialized_end=964
  _globals['_EXPERIMENTINFO']._serialized_start=966
  _globals['_EXPERIMENTINFO']._serialized_end=1083
  _globals['_GETEXPERIMENTLISTRESPONSE']._serialized_start=1085
  _globals['_GETEXPERIMENTLISTRESPONSE']._serialized_end=1165
  _globals['_UPDATERUNNINGEXPERIMENTRESPONSE']._serialized_start=1168
  _globals['_UPDATERUNNINGEXPERIMENTRESPONSE']._serialized_end=1631
  _globals['_UPDATERUNNINGEXPERIMENTRESPONSE_UPDATESCRIPTREPLY']._serialized_start=1303
  _globals['_UPDATERUNNINGEXPERIMENTRESPONSE_UPDATESCRIPTREPLY']._serialized_end=1631
  _globals['_UPDATERUNNINGEXPERIMENTRESPONSE_UPDATESCRIPTREPLY_UPDATESCRIPTRESULT']._serialized_start=1464
  _globals['_UPDATERUNNINGEXPERIMENTRESPONSE_UPDATESCRIPTREPLY_UPDATESCRIPTRESULT']._serialized_end=1631
  _globals['_GETCURRENTPROGRESSRESPONSE']._serialized_start=1634
  _globals['_GETCURRENTPROGRESSRESPONSE']._serialized_end=1830
  _globals['_GETTEMPERATURECONTROLSTATUSRESPONSE']._serialized_start=1832
  _globals['_GETTEMPERATURECONTROLSTATUSRESPONSE']._serialized_end=1942
  _globals['_GETSHAKERCONTROLSTATUSRESPONSE']._serialized_start=1944
  _globals['_GETSHAKERCONTROLSTATUSRESPONSE']._serialized_end=2033
  _globals['_GETCOVERSTATERESPONSE']._serialized_start=2035
  _globals['_GETCOVERSTATERESPONSE']._serialized_end=2109
  _globals['_GETACTUALGASSINGMODERESPONSE']._serialized_start=2111
  _globals['_GETACTUALGASSINGMODERESPONSE']._serialized_end=2193
  _globals['_GETGASPERCENTAGEREQUEST']._serialized_start=2195
  _globals['_GETGASPERCENTAGEREQUEST']._serialized_end=2265
  _globals['_SETTARGETGASPERCENTAGEREQUEST']._serialized_start=2267
  _globals['_SETTARGETGASPERCENTAGEREQUEST']._serialized_end=2367
  _globals['_CULTIVATIONVALUESITEM']._serialized_start=2370
  _globals['_CULTIVATIONVALUESITEM']._serialized_end=2697
  _globals['_CULTIVATIONVALUESITEM_VALUE']._serialized_start=2598
  _globals['_CULTIVATIONVALUESITEM_VALUE']._serialized_end=2697
  _globals['_GETCULTIVATIONVALUESRESPONSE']._serialized_start=2699
  _globals['_GETCULTIVATIONVALUESRESPONSE']._serialized_end=2790
  _globals['_PHCONTROLPARAMS']._serialized_start=2792
  _globals['_PHCONTROLPARAMS']._serialized_end=2901
  _globals['_GETPHCONTROLSTATUSRESPONSE']._serialized_start=2904
  _globals['_GETPHCONTROLSTATUSRESPONSE']._serialized_end=3165
  _globals['_GETPHCONTROLSTATUSRESPONSE_CONTROLSTATUS']._serialized_start=3018
  _globals['_GETPHCONTROLSTATUSRESPONSE_CONTROLSTATUS']._serialized_end=3165
  _globals['_SETTARGETPHREQUEST']._serialized_start=3167
  _globals['_SETTARGETPHREQUEST']._serialized_end=3242
  _globals['_SETPHCONTROLSTATEREQUEST']._serialized_start=3244
  _globals['_SETPHCONTROLSTATEREQUEST']._serialized_end=3330
  _globals['_SETPHCONTROLPARAMSREQUEST']._serialized_start=3332
  _globals['_SETPHCONTROLPARAMSREQUEST']._serialized_end=3452
  _globals['_FEEDREQUEST']._serialized_start=3454
  _globals['_FEEDREQUEST']._serialized_end=3532
  _globals['_SETFEEDCONTROLPARAMSREQUEST']._serialized_start=3535
  _globals['_SETFEEDCONTROLPARAMSREQUEST']._serialized_end=3673
  _globals['_RUNFEEDPULSEREQUEST']._serialized_start=3675
  _globals['_RUNFEEDPULSEREQUEST']._serialized_end=3777
  _globals['_SETLAMWORKMODEREQUEST']._serialized_start=3779
  _globals['_SETLAMWORKMODEREQUEST']._serialized_end=3843
  _globals['_POWER']._serialized_start=3845
  _globals['_POWER']._serialized_end=3882
  _globals['_SETLAMRELATIVEPOWERSREQUEST']._serialized_start=3884
  _globals['_SETLAMRELATIVEPOWERSREQUEST']._serialized_end=3953
  _globals['_GETLAMSTATUSRESPONSE']._serialized_start=3955
  _globals['_GETLAMSTATUSRESPONSE']._serialized_end=4077
  _globals['_SHAKERSTATUS']._serialized_start=4079
  _globals['_SHAKERSTATUS']._serialized_end=4150
  _globals['_TEMPERATURESTATUS']._serialized_start=4152
  _globals['_TEMPERATURESTATUS']._serialized_end=4244
  _globals['_MEASUREMENTSTATUS']._serialized_start=4247
  _globals['_MEASUREMENTSTATUS']._serialized_end=4452
  _globals['_STATUSCOMMENT']._serialized_start=4454
  _globals['_STATUSCOMMENT']._serialized_end=4530
  _globals['_STATUSUPDATESTREAMRESPONSE']._serialized_start=4533
  _globals['_STATUSUPDATESTREAMRESPONSE']._serialized_end=4967
  _globals['_BIOLECTORXTREMOTECONTROL']._serialized_start=5981
  _globals['_BIOLECTORXTREMOTECONTROL']._serialized_end=9834
# @@protoc_insertion_point(module_scope)