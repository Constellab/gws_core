# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from traceback import FrameSummary, extract_tb, format_exc, format_list
from types import ModuleType, TracebackType
from typing import List


class ExceptionHelper():

    @staticmethod
    def filter_traceback(traceback: TracebackType, module_type: ModuleType) -> List[FrameSummary]:
        """Method to filter the traceback only keep frame after the last frame of module_type
        """
        tb_frames = extract_tb(traceback)
        tb_frames.reverse()

        # keep only the frame that are after the last frame of file task_runner.py
        # we want to keep only the stack trace of the task
        filtered_stack_trace: List[FrameSummary] = []

        for frame in tb_frames:
            if frame.filename == module_type.__file__:
                break
            filtered_stack_trace.insert(0, frame)

        return filtered_stack_trace

    @staticmethod
    def sub_traceback_to_str(exception: Exception, module_type: ModuleType) -> str:
        """Method convert a sub section of the stack trace to a string
        """
        filtered_stack_trace = ExceptionHelper.filter_traceback(exception.__traceback__, module_type)

        # if no stack trace, return the complete stack trace
        if len(filtered_stack_trace) == 0:
            return str(format_exc())

        # return the filtered stack trace as string and exception type and message
        return f"{''.join(format_list(filtered_stack_trace))}\n{exception.__class__.__name__} : {str(exception)}"
