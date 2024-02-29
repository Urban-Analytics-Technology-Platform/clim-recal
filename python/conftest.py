import pprint
import sys
from os import PathLike
from pathlib import Path
from typing import Callable, Final

import pytest
from coverage_badge.__main__ import main as gen_cov_badge
from debiasing.debias_wrapper import (
    CALIB_DATES_STR_DEFAULT,
    CMETHODS_FILE_NAME,
    CMETHODS_OUT_FOLDER_DEFAULT,
    DATA_PATH_DEFAULT,
    MOD_FOLDER_DEFAULT,
    OBS_FOLDER_DEFAULT,
    PREPROCESS_FILE_NAME,
    PREPROCESS_OUT_FOLDER_DEFAULT,
    PROCESSESORS_DEFAULT,
    VALID_DATES_STR_DEFAULT,
    CityOptions,
    MethodOptions,
    RunOptions,
    VariableOptions,
)
from numpy import array, random
from utils import (
    ISO_DATE_FORMAT_STR,
    DateType,
    date_range_generator,
    iter_to_tuple_strs,
)
from xarray import DataArray

# Date Range covering leap year
XARRAY_START_DATE_STR: Final[str] = "1980-11-30"
XARRAY_END_DATE_4_DAYS: Final[str] = "1980-12-5"
XARRAY_END_DATE_4_YEARS: Final[str] = "1984-11-30"

GLASGOW_COORDS: Final[tuple[float, float]] = (55.86279, -4.25424)
MANCHESTER_COORDS: Final[tuple[float, float]] = (53.48095, -2.23743)
LONDON_COORDS: Final[tuple[float, float]] = (51.509865, -0.118092)
CITY_COORDS: Final[dict[str, tuple[float, float]]] = {
    "Glasgow": GLASGOW_COORDS,
    "Manchester": MANCHESTER_COORDS,
    "London": LONDON_COORDS,
}


BADGE_PATH: Final[Path] = Path("docs") / "assets" / "coverage.svg"
CLIMATE_DATA_MOUNT_PATH_LINUX: Final[Path] = Path("/mnt/vmfileshare/ClimateData")
CLIMATE_DATA_MOUNT_PATH_MACOS: Final[Path] = Path("/Volumes/vmfileshare/ClimateData")
TEST_PATH = Path().absolute()
PYTHON_DIR_NAME: Final[Path] = Path("python")
MODULE_NAMES: Final[tuple[PathLike, ...]] = ("debiasing",)

CLI_PREPROCESS_DEFAULT_COMMAND_TUPLE_CORRECT: Final[tuple[str, ...]] = (
    "python",
    PREPROCESS_FILE_NAME,
    "--mod",
    DATA_PATH_DEFAULT / MOD_FOLDER_DEFAULT / CityOptions.default(),
    "--obs",
    DATA_PATH_DEFAULT / OBS_FOLDER_DEFAULT / CityOptions.default(),
    "-v",
    VariableOptions.default(),
    "-r",
    RunOptions.default(),
    "--out",
    (
        DATA_PATH_DEFAULT
        / PREPROCESS_OUT_FOLDER_DEFAULT
        / CityOptions.default()
        / RunOptions.default()
        / VariableOptions.default()
    ),
    "--calib_dates",
    CALIB_DATES_STR_DEFAULT,
    "--valid_dates",
    VALID_DATES_STR_DEFAULT,
)

CLI_PREPROCESS_DEFAULT_COMMAND_TUPLE_STR_CORRECT: Final[
    tuple[str, ...]
] = iter_to_tuple_strs(CLI_PREPROCESS_DEFAULT_COMMAND_TUPLE_CORRECT)

CLI_PREPROCESS_DEFAULT_COMMAND_STR_CORRECT: Final[str] = " ".join(
    CLI_PREPROCESS_DEFAULT_COMMAND_TUPLE_STR_CORRECT
)

CLI_CMETHODS_DEFAULT_COMMAND_TUPLE_CORRECT: Final[tuple[str, ...]] = (
    "python",
    CMETHODS_FILE_NAME,
    "--input_data_folder",
    CLI_PREPROCESS_DEFAULT_COMMAND_TUPLE_CORRECT[11],
    "--out",
    (
        DATA_PATH_DEFAULT
        / CMETHODS_OUT_FOLDER_DEFAULT
        / CityOptions.default()
        / RunOptions.default()
    ).resolve(),
    "--method",
    MethodOptions.default(),
    "-v",
    VariableOptions.default(),
    "-p",
    PROCESSESORS_DEFAULT,
)

CLI_CMETHODS_DEFAULT_COMMAND_TUPLE_STR_CORRECT: Final[
    tuple[str, ...]
] = iter_to_tuple_strs(CLI_CMETHODS_DEFAULT_COMMAND_TUPLE_CORRECT)

CLI_CMETHODS_DEFAULT_COMMAND_STR_CORRECT: Final[str] = " ".join(
    CLI_CMETHODS_DEFAULT_COMMAND_TUPLE_STR_CORRECT
)


MOD_FOLDER_FILES_COUNT_CORRECT: Final[int] = 1478
OBS_FOLDER_FILES_COUNT_CORRECT: Final[int] = MOD_FOLDER_FILES_COUNT_CORRECT
PREPROCESS_OUT_FOLDER_FILES_COUNT_CORRECT: Final[int] = 4


@pytest.fixture
def is_platform_darwin() -> bool:
    """Check if `sys.platform` is `Darwin` (macOS)."""
    return sys.platform.startswith("darwin")


@pytest.fixture
def climate_data_mount_path(is_platform_darwin: bool) -> Path:
    """Return likely climate data mount path based on operating system.

    Parameters
    ----------
    is_platform_darwin
        Calls fixture `is_platform_darwin`.

    Returns
    -------
    The `Path` climate data would likely be mounted to.
    """
    if is_platform_darwin:
        return CLIMATE_DATA_MOUNT_PATH_MACOS
    else:
        return CLIMATE_DATA_MOUNT_PATH_LINUX


@pytest.fixture
def is_climate_data_mounted(climate_data_mount_path) -> bool:
    """Check if CLIMATE_DATA_MOUNT_PATH is mounted."""
    return climate_data_mount_path.exists()


@pytest.fixture(autouse=True)
def ensure_python_path() -> None:
    """Return path for test running."""
    if not set(MODULE_NAMES) <= set(path.name for path in TEST_PATH.iterdir()):
        raise ValueError(
            f"'clim-recal' python tests must be "
            f"run in 'clim-recal/{PYTHON_DIR_NAME}', "
            f"not '{TEST_PATH.absolute()}'"
        )


@pytest.fixture
def preprocess_out_folder_files_count_correct() -> int:
    """Return `PREPROCESS_OUT_FOLDER_FILES_COUNT_CORRECT`."""
    return PREPROCESS_OUT_FOLDER_FILES_COUNT_CORRECT


@pytest.fixture
def xarray_spatial_temporal() -> (
    Callable[[str, str, dict[str, tuple[float, float]]], DataArray]
):
    """Generate a `xarray` spatial time series 1980-11-30 to 1984-11-30.

    See https://xarray-spatial.org/user_guide/local.html?highlight=time
    """

    def _xarray_spatial_temporal(
        start_date_str: str = XARRAY_START_DATE_STR,
        end_date_str: str = XARRAY_END_DATE_4_YEARS,
        coordinates: dict[str, tuple[float, float]] = CITY_COORDS,
        **kwargs,
    ) -> DataArray:
        dates: list[DateType] = list(
            date_range_generator(
                start_date=start_date_str,
                end_date=end_date_str,
                start_format_str=ISO_DATE_FORMAT_STR,
                end_format_str=ISO_DATE_FORMAT_STR,
                **kwargs,
            )
        )
        random.seed(0)  # ensure results are predictable
        data: array = random.rand(len(dates), len(coordinates))
        spaces: list[str] = list(coordinates.keys())
        # If useful, add lat/lon (currently not working)
        # lat: list[float] = [coord[0] for coord in coordinates.values()]
        # lon: list[float] = [coord[1] for coord in coordinates.values()]
        return DataArray(
            data,
            coords=[
                dates,
                spaces,
            ],
            dims=[
                "time",
                "space",
            ],
            # If useful, add lat/lon (currently not working)
            # coords=[dates, spaces, lon, lat],
            # dims=["time", "space", "lon", "lat"]
        )

    return _xarray_spatial_temporal


@pytest.fixture
def xarray_spatial_4_days(
    xarray_spatial_temporal: Callable,
    end_date_str: str = XARRAY_END_DATE_4_DAYS,
) -> DataArray:
    """Generate a `xarray` spatial time series 1980-11-30 to 1980-12-05."""
    return xarray_spatial_temporal(end_date_str=end_date_str)


@pytest.fixture
def xarray_spatial_4_years(
    xarray_spatial_temporal: Callable,
    end_date_str: str = XARRAY_END_DATE_4_YEARS,
) -> DataArray:
    """Generate a `xarray` spatial time series 1980-11-30 to 1984-11-30."""
    return xarray_spatial_temporal(end_date_str=end_date_str)


@pytest.fixture(autouse=True)
def doctest_auto_fixtures(
    doctest_namespace: dict,
    is_platform_darwin: bool,
    is_climate_data_mounted: bool,
    preprocess_out_folder_files_count_correct: int,
) -> None:
    """Elements to add to default `doctest` namespace."""
    doctest_namespace[
        "CLI_PREPROCESS_DEFAULT_COMMAND_TUPLE_CORRECT"
    ] = CLI_PREPROCESS_DEFAULT_COMMAND_TUPLE_CORRECT
    doctest_namespace[
        "CLI_PREPROCESS_DEFAULT_COMMAND_STR_CORRECT"
    ] = CLI_PREPROCESS_DEFAULT_COMMAND_STR_CORRECT
    doctest_namespace[
        "CLI_PREPROCESS_DEFAULT_COMMAND_TUPLE_STR_CORRECT"
    ] = CLI_PREPROCESS_DEFAULT_COMMAND_TUPLE_STR_CORRECT
    doctest_namespace["MOD_FOLDER_FILES_COUNT_CORRECT"] = MOD_FOLDER_FILES_COUNT_CORRECT
    doctest_namespace["OBS_FOLDER_FILES_COUNT_CORRECT"] = OBS_FOLDER_FILES_COUNT_CORRECT
    doctest_namespace[
        "PREPROCESS_OUT_FOLDER_FILES_COUNT_CORRECT"
    ] = preprocess_out_folder_files_count_correct
    doctest_namespace[
        "CLI_CMEHTODS_DEFAULT_COMMAND_TUPLE_STR_CORRECT"
    ] = CLI_CMETHODS_DEFAULT_COMMAND_TUPLE_STR_CORRECT
    doctest_namespace[
        "CLI_CMETHODS_DEFAULT_COMMAND_TUPLE_CORRECT"
    ] = CLI_CMETHODS_DEFAULT_COMMAND_TUPLE_CORRECT
    doctest_namespace[
        "CLI_CMETHODS_DEFAULT_COMMAND_STR_CORRECT"
    ] = CLI_CMETHODS_DEFAULT_COMMAND_STR_CORRECT
    doctest_namespace["is_platform_darwin"] = is_platform_darwin
    doctest_namespace["is_climate_data_mounted"] = is_climate_data_mounted
    doctest_namespace["pprint"] = pprint
    doctest_namespace["pytest"] = pytest
    doctest_namespace["xarray_spatial_4_days"] = xarray_spatial_4_days
    doctest_namespace["xarray_spatial_4_years"] = xarray_spatial_4_years


def pytest_sessionfinish(session, exitstatus):
    """Generate badges for docs after tests finish."""
    if exitstatus == 0:
        BADGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        gen_cov_badge(["-o", f"{BADGE_PATH}", "-f"])
