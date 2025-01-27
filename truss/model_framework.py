from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List

import yaml
from truss.constants import CONFIG_FILE, TEMPLATES_DIR
from truss.model_inference import infer_python_version
from truss.truss_config import DEFAULT_EXAMPLES_FILENAME, TrussConfig
from truss.types import ModelFrameworkType
from truss.utils import copy_file_path, copy_tree_path


class ModelFramework(ABC):
    @abstractmethod
    def typ(self) -> ModelFrameworkType:
        pass

    @abstractmethod
    def infer_requirements(self):
        """Mapping of requirements.txt line by name of the requirement.

        e.g. {'tensorflow': 'tensorflow==1.0.0'}
        """
        pass

    def requirements_txt(self) -> List[str]:
        return list(self.infer_requirements().values())

    @abstractmethod
    def serialize_model_to_directory(self, model, target_directory: Path):
        pass

    @abstractmethod
    def model_metadata(self, model) -> Dict[str, str]:
        pass

    def model_type(self, model) -> str:
        return "Model"

    def model_name(self, model) -> str:
        return None

    def to_truss(self, model, target_directory: Path) -> str:
        """Exports in-memory model to a Truss, in a target directory."""
        model_binary_dir = target_directory / "data" / "model"
        model_binary_dir.mkdir(parents=True, exist_ok=True)

        # Serialize model and write it
        self.serialize_model_to_directory(model, model_binary_dir)
        template_path = TEMPLATES_DIR / self.typ().value
        copy_tree_path(template_path / "model", target_directory / "model")
        examples_path = template_path / DEFAULT_EXAMPLES_FILENAME
        target_examples_path = target_directory / DEFAULT_EXAMPLES_FILENAME
        if examples_path.exists():
            copy_file_path(examples_path, target_examples_path)
        else:
            target_examples_path.touch()

        python_version = infer_python_version()

        # Create config
        config = TrussConfig(
            model_name=self.model_name(model),
            model_type=self.model_type(model),
            model_framework=self.typ(),
            model_metadata=self.model_metadata(model),
            requirements=self.requirements_txt(),
            python_version=python_version,
        )
        with (target_directory / CONFIG_FILE).open("w") as config_file:
            yaml.dump(config.to_dict(), config_file)

    def supports_model_class(self, model_class) -> bool:
        pass
