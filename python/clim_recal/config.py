import subprocess
import warnings
from dataclasses import dataclass, field
from logging import DEBUG, FileHandler, getLogger
from os import PathLike, chdir, cpu_count
from pathlib import Path
from typing import Any, Final, Sequence, TypedDict

from osgeo import gdal
from tqdm import TqdmExperimentalWarning, tqdm

from .convert import RAW_CPM_PATH, RAW_HADS_PATH, CPMConvertManager, HADsConvertManager
from .crop import CPMRegionCropManager, HADsRegionCropManager
from .debiasing.debias_wrapper import BaseRunConfig, RunConfig, RunConfigType
from .utils.core import console, product_dict, results_path
from .utils.data import (
    CPM_NAME,
    CPM_OUTPUT_PATH,
    HADS_AND_CPM,
    HADS_NAME,
    HADS_OUTPUT_PATH,
    ClimDataTypeTuple,
    MethodOptions,
    RegionOptions,
    RunOptions,
    VariableOptions,
)

logger = getLogger(__name__)

warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)


DEFAULT_OUTPUT_PATH: Final[Path] = Path("clim-recal-runs")
DEFAULT_CONVERT_FOLDER: Final[Path] = Path("convert")
DEFAULT_CROPS_FOLDER: Final[Path] = Path("crops")
DEFAULT_CPUS: Final[int] = 2


class ClimRecalRunsConfigType(TypedDict):
    """Lists of parameters to generate `RunConfigType` instances."""

    regions: Sequence[RegionOptions] | None
    variables: Sequence[VariableOptions]
    runs: Sequence[RunOptions]
    methods: Sequence[MethodOptions]


ClimRecalRunResultsType = dict[RunConfig, dict[str, subprocess.CompletedProcess]]


# Todo: replace ValueError with clearer Exception.
class ClimRecanConfigError(Exception):
    pass


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
    convert_folder
        `Path` to append to `output_path` for resampling result files.
    crops_folder
        `Path` to append to `output_path` for cropped convert files.
    hads_output_folder
        `Path` to append to `output_path` / `convert_folder` for resampling `HADs` files and to `output_path` / `crop_folder` for crops.
    cpm_output_folder
        `Path` to append to `output_path` / `convert_folder` for resampling `CPM` files and to `output_path` / `crop_folder` for crops.
    cpm_kwargs
        A `dict` of parameters to pass to a `CPMConvertManager`.
    hads_kwargs
        A `dict` of parameters to pass to `HADsConvertManager`.
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
    'set_cpm_for_coord_alignment' for 'HADs' not speficied.
    Defaulting to 'self.cpm_input_path': '.../ClimateData/Raw/UKCP2.2'
    >>> run_config
    <ClimRecalConfig(variables_count=1, runs_count=1, regions_count=2,
                     methods_count=1, cpm_folders_count=1,
                     hads_folders_count=1, convert_start_index=0,
                     convert_stop_index=None, crop_start_index=0,
                     crop_stop_index=None, cpus=1)>
    """

    variables: Sequence[VariableOptions] = (VariableOptions.default(),)
    runs: Sequence[RunOptions] = (RunOptions.default(),)
    regions: Sequence[RegionOptions] | None = (RegionOptions.default(),)
    methods: Sequence[MethodOptions] = (MethodOptions.default(),)
    convert: bool = True
    crop: bool = True
    multiprocess: bool = False
    clim_types: ClimDataTypeTuple = HADS_AND_CPM
    cpus: int | None = DEFAULT_CPUS
    hads_input_path: PathLike = RAW_HADS_PATH
    cpm_input_path: PathLike = RAW_CPM_PATH
    output_path: PathLike = DEFAULT_OUTPUT_PATH
    convert_folder: PathLike = DEFAULT_CONVERT_FOLDER
    crops_folder: PathLike = DEFAULT_CROPS_FOLDER
    hads_output_folder: PathLike = HADS_OUTPUT_PATH
    cpm_output_folder: PathLike = CPM_OUTPUT_PATH
    cpm_kwargs: dict = field(default_factory=dict)
    hads_kwargs: dict = field(default_factory=dict)
    cpm_crop_kwargs: dict = field(default_factory=dict)
    hads_crop_kwargs: dict = field(default_factory=dict)
    convert_start_index: int = 0
    convert_stop_index: int | None = None
    crop_start_index: int = 0
    crop_stop_index: int | None = None
    calc_start_index: int = 0
    calc_stop_index: int | None = None
    add_local_dated_results_path: bool = True
    add_local_dated_crops_path: bool = True
    local_dated_results_path_prefix: str = "run"
    local_dated_crops_path_prefix: str = "crop"
    cpm_for_coord_alignment: PathLike | None = None
    process_cmp_for_coord_alignment: bool = False
    cpm_for_coord_alignment_path_converted: bool = False
    log_file: bool = True
    file_log_level: int = DEBUG
    debug_mode: bool = False

    @property
    def convert_path(self) -> Path:
        """The convert_path property."""
        return Path(self.exec_path) / self.convert_folder

    @property
    def crops_path(self) -> Path:
        """The convert_path property."""
        return Path(self.exec_path) / self.crops_folder

    @property
    def include_hads(self) -> bool:
        """Whether `HADS_NAME` is in `self.clim_types`."""
        return HADS_NAME in self.clim_types

    @property
    def include_cpm(self) -> bool:
        """Whether `CPM_NAME` is in `self.clim_types`."""
        return CPM_NAME in self.clim_types

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
    def convert_hads_path(self) -> Path:
        """The convert_hads_path property."""
        return self.convert_path / self.hads_output_folder

    @property
    def convert_cpm_path(self) -> Path:
        """The convert_hads_path property."""
        return self.convert_path / self.cpm_output_folder

    @property
    def cropped_hads_path(self) -> Path:
        """The convert_hads_path property."""
        return self.crops_path / self.hads_output_folder

    @property
    def cropped_cpm_path(self) -> Path:
        """The convert_cpm_path property."""
        return self.crops_path / self.cpm_output_folder

    @property
    def log_path(self) -> Path:
        if not hasattr(self, "_log_path"):
            self._log_path = results_path(
                name="run",
                path=self.exec_path,
                extension="log",
                mkdir=True,
            )
            self._log_path.touch()
        return self._log_path

    def _init_logger(self) -> Path | None:
        """Inititialise logger for current run."""
        if self.log_file:
            self.file_log_handler: FileHandler = FileHandler(self.log_path)
            self.file_log_handler.setLevel(self.file_log_level)
            logger.addHandler(self.file_log_handler)
            return self.log_path

    def __post_init__(self) -> None:
        """Initiate related `HADs` and `CPM` managers.

        Notes
        -----
        The variagles passed to `CPMConvertManager` do not apply
        `VariableOptions.cpm_values()`, that occurs within `CPMConvertManager`
        for ease of comparability with HADs.
        """
        if self.log_file:
            self._init_logger()
        gdal.UseExceptions() if self.debug_mode else gdal.DontUseExceptions()
        if self.convert:
            if self.include_cpm:
                self.cpm_manager = CPMConvertManager(
                    input_paths=self.cpm_input_path,
                    variables=self.variables,
                    runs=self.runs,
                    output_paths=self.convert_cpm_path,
                    start_index=self.convert_start_index,
                    stop_index=self.convert_stop_index,
                    start_calc_index=self.calc_start_index,
                    stop_calc_index=self.calc_stop_index,
                    **self.cpm_kwargs,
                )
            if self.include_hads:
                self.set_cpm_for_coord_alignment()
                self.hads_manager = HADsConvertManager(
                    input_paths=self.hads_input_path,
                    variables=self.variables,
                    output_paths=self.convert_hads_path,
                    start_index=self.convert_start_index,
                    stop_index=self.convert_stop_index,
                    start_calc_index=self.calc_start_index,
                    stop_calc_index=self.calc_stop_index,
                    cpm_for_coord_alignment=self.cpm_for_coord_alignment,
                    cpm_for_coord_alignment_path_converted=self.cpm_for_coord_alignment_path_converted,
                    **self.hads_kwargs,
                )
        if self.crop and self.regions:
            if self.include_cpm:
                self.cpm_crop_manager = CPMRegionCropManager(
                    input_paths=self.cpm_output_folder,
                    crop_regions=tuple(self.regions),
                    variables=self.variables,
                    runs=self.runs,
                    output_paths=self.cropped_cpm_path,
                    start_index=self.crop_start_index,
                    stop_index=self.crop_stop_index,
                    start_calc_index=self.calc_start_index,
                    stop_calc_index=self.calc_stop_index,
                    check_input_paths_exist=False,
                    **self.cpm_crop_kwargs,
                )
            if self.include_hads:
                self.hads_crop_manager = HADsRegionCropManager(
                    input_paths=self.hads_output_folder,
                    crop_regions=tuple(self.regions),
                    variables=self.variables,
                    output_paths=self.cropped_hads_path,
                    start_index=self.crop_start_index,
                    stop_index=self.crop_stop_index,
                    start_calc_index=self.calc_start_index,
                    stop_calc_index=self.calc_stop_index,
                    check_input_paths_exist=False,
                    **self.hads_crop_kwargs,
                )
        self.total_cpus: int | None = cpu_count()
        if self.cpus == None or (self.total_cpus and self.cpus >= self.total_cpus):
            self.cpus = 1 if not self.total_cpus else self.total_cpus - 1

    def set_cpm_for_coord_alignment(self) -> None:
        """If `cpm_for_coord_alignment` is `None` use `self.cpm_input_path`.

        It would be more efficient to use `self.convert_cpm_path` as
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
            f"cpm_folders_count={len(self.cpm_manager) if hasattr(self, 'cpm_manager') else None}, "
            f"hads_folders_count={len(self.hads_manager) if hasattr(self, 'hads_manager') else None}, "
            f"convert_start_index={self.convert_start_index}, "
            f"convert_stop_index={self.convert_stop_index if self.convert_stop_index else 'None'}, "
            f"crop_start_index={self.crop_start_index}, "
            f"crop_stop_index={self.crop_stop_index if self.crop_stop_index else 'None'}, "
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
        return RunConfig(
            command_dir=self.command_dir,
            variable=self._first_conf_variable,
            run=self._first_conf_run,
            region=self._first_conf_region,
            method=self._first_conf_method,
            run_prefix=self.run_prefix,
            preprocess_data_file=self.preprocess_data_file,
            run_cmethods_file=self.run_cmethods_file,
            data_path=self.data_path,
            mod_folder=self.mod_folder,
            obs_folder=self.obs_folder,
            preprocess_out_folder=self.preprocess_out_folder,
            cmethods_out_folder=self.cmethods_out_folder,
            calib_date_start=self.calib_date_start,
            calib_date_end=self.calib_date_end,
            valid_date_start=self.valid_date_start,
            valid_date_end=self.valid_date_end,
            processors=self.processors,
            date_format_str=self.date_format_str,
            date_split_str=self.date_split_str,
        )

    def run_models(self) -> ClimRecalRunResultsType:
        """Run all specified models.

        Examples
        --------
        >>> clim_runner: ClimRecalConfig = getfixture('clim_runner')
        >>> runs: dict[tuple, dict] = clim_runner.run_models()
        >>> pprint(tuple(runs.keys()))
        (('Glasgow', 'tasmax', '05', 'quantile_delta_mapping'),
         ('Manchester', 'tasmax', '05', 'quantile_delta_mapping'))
        """
        initial_folder: Path = Path().resolve()
        chdir(self._base_run_config.command_path)
        run_results: ClimRecalRunResultsType = {}

        for model_config in tqdm(self.model_configs):
            preprocess_run: subprocess.CompletedProcess = subprocess.run(
                self._base_run_config.to_cli_preprocess_tuple_strs(
                    variable=model_config["variable"],
                    run=model_config["run"],
                    region=model_config["region"],
                ),
                capture_output=True,
                text=True,
            )
            cmethods_run: subprocess.CompletedProcess = subprocess.run(
                self._base_run_config.to_cli_run_cmethods_tuple_strs(
                    region=model_config["region"],
                    run=model_config["run"],
                    variable=model_config["variable"],
                    method=model_config["method"],
                ),
                capture_output=True,
                text=True,
            )
            run_results[tuple(model_config.values())] = {
                "preprocess_run": preprocess_run,
                "cmethods_run": cmethods_run,
            }
        chdir(initial_folder)
        return run_results

    @property
    def command_path(self) -> Path:
        """Return command path relative to running tests."""
        return (Path() / self.command_dir).absolute()
