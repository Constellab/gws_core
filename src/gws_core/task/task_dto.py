

from typing import Dict, Optional

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.io.io_specs import IOSpecsDTO
from gws_core.model.typing_dto import TypingFullDTO


class TaskTypingDTO(TypingFullDTO):
    input_specs: Optional[IOSpecsDTO] = None
    output_specs: Optional[IOSpecsDTO] = None
    config_specs: Optional[Dict[str, ParamSpecDTO]] = None
    additional_data: Optional[dict] = None

    def to_markdown(self) -> str:
        markdown = super().to_markdown()

        if self.input_specs and len(self.input_specs.specs) > 0:
            markdown += '\n\n**Inputs:**\n'
            markdown += self.input_specs.to_markdown()
        else:
            markdown += '\n\nNo input.'

        if self.output_specs and len(self.output_specs.specs) > 0:
            markdown += '\n\n**Outputs:**\n'
            markdown += self.output_specs.to_markdown()
        else:
            markdown += '\n\nNo output.'

        if self.config_specs:
            markdown += '\n\n**Configurations:**\n'
            for spec in self.config_specs.values():
                markdown += spec.to_markdown() + "\n"
        else:
            markdown += '\n\nNo configuration.'

        return markdown
