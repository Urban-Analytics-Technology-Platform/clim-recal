import subprocess
import warnings
from dataclasses import dataclass, field
from os import PathLike, cpu_count
from pathlib import Path
from typing import Any, Final, Sequence, TypedDict

from osgeo import gdal
from tqdm import TqdmExperimentalWarning

from .resample import (
    CPM_OUTPUT_LOCAL_PATH,
    HADS_OUTPUT_LOCAL_PATH,
    RAW_CPM_PATH,
    RAW_HADS_PATH,
    CPMResamplerManager,
    HADsResamplerManager,
)
from .utils.core import console, product_dict, results_path
from .utils.data import MethodOptions, RegionOptions, RunOptions, VariableOptions

warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)


DEFAULT_OUTPUT_PATH: Final[Path] = Path("clim-recal-runs")
DEFAULT_RESAMPLE_FOLDER: Final[Path] = Path("resample")
DEFAULT_CROPS_FOLDER: Final[Path] = Path("crops")
DEFAULT_CPUS: Final[int] = 2


class ClimRecalRunsConfigType(TypedDict):
    """Lists of parameters to generate `RunConfigType` instances."""

    regions: Sequence[RegionOptions] | None
    variables: Sequence[VariableOptions]
    runs: Sequence[RunOptions]
    methods: Sequence[MethodOptions]


@dataclass
class BaseRunConfig:
    """Manage creating command line scripts to run `debiasing` `cli`."""


@dataclass
class RunConfig(BaseRunConfig):
    """Manage creating command line scripts to run `debiasing` `cli`."""


class RunConfigType(TypedDict):
    """Parameters needed for a model run."""


ClimRecalRunResultsType = dict[RunConfig, dict[str, subprocess.CompletedProcess]]


@dataclass
class ClimRecalConfig(BaseRunConfig):
    """Manage creating command line scripts to run `debiasing` `cli`.

    Attributes
    ----------
    variables
        Variables to include in the model, eg. `tasmax`, `tasmin`.
    runs
        Which model runs to include, eg. "01", "08", "11".
    regions
        Which regions to crop both HADs and CPM data to.
    methods
        Which debiasing methods to apply.
    multiprocess
        Whether to use `multiprocess` where available
    cpus
        Number of cpus to use if multiprocessing
    output_path
        `Path` to save all intermediate and final results to.
    resample_folder
        `Path` to append to `output_path` for resampling result files.
    crops_folder
        `Path` to append to `output_path` for cropped resample files.
    hads_output_folder
        `Path` to append to `output_path` / `resample_folder` for resampling `HADs` files and to `output_path` / `crop_folder` for crops.
    cpm_output_folder
        `Path` to append to `output_path` / `resample_folder` for resampling `CPM` files and to `output_path` / `crop_folder` for crops.
    cpm_kwargs
        A `dict` of parameters to pass to a `CPMResamplerManager`.
    hads_kwargs
        A `dict` of parameters to pass to `HADsResamplerManager`.
    cpm_for_coord_alignment
        A `Path` to a `CPM` file to align `HADs` coordinates to.
    debug_mode
        Set to `True` to add more detailed debug logs, including `GDAL`.

    Examples
    --------
    >>> if not is_data_mounted:
    ...     pytest.skip(mount_doctest_skip_message)
    >>> run_config: ClimRecalConfig = ClimRecalConfig(
    ...     regions=('Manchester', 'Glasgow'),
    ...     output_path=test_runs_output_path,
    ...     cpus=1)
    >>> run_config
    <ClimRecalConfig(variables_count=1, runs_count=1, regions_count=2,
                     methods_count=1, cpm_folders_count=1,
                     hads_folders_count=1, start_index=0,
                     stop_index=None, cpus=1)>
    """

    variables: Sequence[VariableOptions] = (VariableOptions.default(),)
    runs: Sequence[RunOptions] = (RunOptions.default(),)
    regions: Sequence[RegionOptions] | None = (RegionOptions.default(),)
    methods: Sequence[MethodOptions] = (MethodOptions.default(),)
    multiprocess: bool = False
    cpus: int | None = DEFAULT_CPUS
    hads_input_path: PathLike = RAW_HADS_PATH
    cpm_input_path: PathLike = RAW_CPM_PATH
    output_path: PathLike = DEFAULT_OUTPUT_PATH
    resample_folder: PathLike = DEFAULT_RESAMPLE_FOLDER
    crops_folder: PathLike = DEFAULT_CROPS_FOLDER
    hads_output_folder: PathLike = HADS_OUTPUT_LOCAL_PATH
    cpm_output_folder: PathLike = CPM_OUTPUT_LOCAL_PATH
    cpm_kwargs: dict = field(default_factory=dict)
    hads_kwargs: dict = field(default_factory=dict)
    start_index: int = 0
    stop_index: int | None = None
    add_local_dated_results_path: bool = True
    add_local_dated_crops_path: bool = True
    local_dated_results_path_prefix: str = "run"
    local_dated_crops_path_prefix: str = "crop"
    cpm_for_coord_alignment: PathLike | None = None
    process_cmp_for_coord_alignment: bool = False
    cpm_for_coord_alignment_path_converted: bool = False
    debug_mode: bool = False

    @property
    def resample_path(self) -> Path:
        """The resample_path property."""
        return Path(self.exec_path) / self.resample_folder

    @property
    def crops_path(self) -> Path:
        """The resample_path property."""
        return Path(self.exec_path) / self.crops_folder

    @property
    def exec_path(self) -> Path:
        """Path to save preparation and intermediate files.

        Examples
        --------
        >>> clim_runner: ClimRecalConfig = getfixture('clim_runner')
        >>> print(clim_runner.exec_path)
        <BLANKLINE>
        ...test-run-results.../run...
        >>> clim_runner.add_local_dated_results_path = False
        >>> print(clim_runner.exec_path)
        <BLANKLINE>
        ...test-run-results...
        """
        if self.add_local_dated_results_path:
            assert self.dated_results_path
            return self.dated_results_path
        else:
            return Path(self.output_path)

    @property
    def dated_results_path(self) -> Path | None:
        """Return a time stamped path if `add_local_dated_results_path` is `True`.

        Examples
        --------
        >>> clim_runner: ClimRecalConfig = getfixture('clim_runner')
        >>> print(clim_runner.dated_results_path)
        <BLANKLINE>
        ...test-run-results.../run...
        >>> clim_runner.add_local_dated_results_path = False
        >>> print(clim_runner.dated_results_path)
        None
        """
        if self.add_local_dated_results_path:
            return self.output_path / results_path(
                self.local_dated_results_path_prefix, mkdir=True
            )
        else:
            return None

    @property
    def dated_crops_path(self) -> Path | None:
        """Return a time stamped path if `add_local_dated_crops_path` is `True`.

        Examples
        --------
        >>> clim_runner: ClimRecalConfig = getfixture('clim_runner')
        >>> print(clim_runner.dated_crops_path)
        <BLANKLINE>
        ...test-run-results.../crop...
        >>> clim_runner.add_local_dated_crops_path = False
        >>> print(clim_runner.dated_crops_path)
        None
        """
        if self.add_local_dated_crops_path:
            return self.output_path / results_path(
                self.local_dated_crops_path_prefix, mkdir=True
            )
        else:
            return None

    @property
    def resample_hads_path(self) -> Path:
        """The resample_hads_path property."""
        return self.resample_path / self.hads_output_folder

    @property
    def resample_cpm_path(self) -> Path:
        """The resample_hads_path property."""
        return self.resample_path / self.cpm_output_folder

    @property
    def cropped_hads_path(self) -> Path:
        """The resample_hads_path property."""
        return self.crops_path / self.hads_output_folder

    @property
    def cropped_cpm_path(self) -> Path:
        """The resample_cpm_path property."""
        return self.crops_path / self.cpm_output_folder

    def __post_init__(self) -> None:
        """Initiate related `HADs` and `CPM` managers.

        Notes
        -----
        The variagles passed to `CPMResamplerManager` do not apply
        `VariableOptions.cpm_values()`, that occurs within `CPMResamplerManager`
        for ease of comparability with HADs.
        """
        gdal.UseExceptions() if self.debug_mode else gdal.DontUseExceptions()
        self.cpm_manager = CPMResamplerManager(
            input_paths=self.cpm_input_path,
            variables=self.variables,
            runs=self.runs,
            resample_paths=self.resample_cpm_path,
            crop_paths=self.crops_path,
            start_index=self.start_index,
            stop_index=self.stop_index,
            **self.cpm_kwargs,
        )
        self.set_cpm_for_coord_alignment()
        self.hads_manager = HADsResamplerManager(
            input_paths=self.hads_input_path,
            variables=self.variables,
            resample_paths=self.resample_hads_path,
            crop_paths=self.crops_path,
            start_index=self.start_index,
            stop_index=self.stop_index,
            cpm_for_coord_alignment=self.cpm_for_coord_alignment,
            cpm_for_coord_alignment_path_converted=self.cpm_for_coord_alignment_path_converted,
            **self.hads_kwargs,
        )
        self.total_cpus: int | None = cpu_count()
        if self.cpus == None or (self.total_cpus and self.cpus >= self.total_cpus):
            self.cpus = 1 if not self.total_cpus else self.total_cpus - 1

    def set_cpm_for_coord_alignment(self) -> None:
        """If `cpm_for_coord_alignment` is `None` use `self.cpm_input_path`.

        It would be more efficient to use `self.resample_cpm_path` as
        long as that option is used, but support cases of only
        """
        if not self.cpm_for_coord_alignment:
            if self.cpm_input_path:
                console.print(
                    "'set_cpm_for_coord_alignment' for 'HADs' not speficied.\n"
                    f"Defaulting to 'self.cpm_input_path': '{self.cpm_input_path}'"
                )
                self.cpm_for_coord_alignment = self.cpm_input_path
            else:
                raise ValueError(
                    f"Neither required 'self.cpm_for_coord_alignment' nor backup "
                    f"'self.cpm_input_path' provided for {self}"
                )

    def __repr__(self) -> str:
        """Summary of `self` configuration as a `str`."""
        return (
            f"<{self.__class__.__name__}("
            f"variables_count={len(self.variables)}, "
            f"runs_count={len(self.runs)}, "
            f"regions_count={len(self.regions) if self.regions else None}, "
            f"methods_count={len(self.methods)}, "
            f"cpm_folders_count={len(self.cpm_manager)}, "
            f"hads_folders_count={len(self.hads_manager)}, "
            f"start_index={self.start_index}, "
            f"stop_index={self.stop_index if self.stop_index else 'None'}, "
            f"cpus={self.cpus})>"
        )

    @property
    def model_vars(self) -> ClimRecalRunsConfigType:
        """Return provided run configurations.

        Examples
        --------
        >>> clim_runner: ClimRecalConfig = getfixture('clim_runner')
        >>> pprint(clim_runner.model_vars)
        {'methods': ('quantile_delta_mapping',),
         'regions': ('Glasgow', 'Manchester'),
         'runs': ('05',),
         'variables': ('tasmax',)}
        """
        return ClimRecalRunsConfigType(
            regions=self.regions,
            variables=self.variables,
            runs=self.runs,
            methods=self.methods,
        )

    @property
    def model_configs(self) -> tuple[RunConfigType, ...]:
        """`tuple` of all model `RunConfigType` runs.

        Examples
        --------
        >>> clim_runner: ClimRecalConfig = getfixture('clim_runner')
        >>> pprint(clim_runner.model_configs)
        ({'method': 'quantile_delta_mapping',
          'region': 'Glasgow',
          'run': '05',
          'variable': 'tasmax'},
         {'method': 'quantile_delta_mapping',
          'region': 'Manchester',
          'run': '05',
          'variable': 'tasmax'})
        """
        return tuple(
            RunConfigType(**params)
            for params in product_dict(
                region=self.regions,
                variable=self.variables,
                run=self.runs,
                method=self.methods,
            )
        )

    def _get_first_or_none(self, attr_name) -> Any | None:
        """Get the first value of self.name if iterable, else None."""
        assert hasattr(self, attr_name)
        val: Any | None = getattr(self, attr_name)
        if val is None:
            return None
        elif isinstance(val, Sequence):
            assert len(val) > 0
            return val[0]
        else:
            raise ValueError(f"{self} attribute should be iterable, not: '{val}'")

    @property
    def _first_conf_variable(self) -> VariableOptions:
        """Return the first `self.variables` value."""
        return self.variables[0]

    @property
    def _first_conf_run(self) -> RunOptions:
        """Return the first `self.variables` value."""
        return self.runs[0]

    @property
    def _first_conf_method(self) -> MethodOptions:
        """Return the first `self.variables` value."""
        return self.methods[0]

    @property
    def _first_conf_region(self) -> VariableOptions | None:
        """Return the first `self.variables` value."""
        return self._get_first_or_none(attr_name="regions")

    @property
    def _base_run_config(self) -> RunConfig:
        """Retun a base `RunConfig` from `self` attributes."""
        return RunConfig()
