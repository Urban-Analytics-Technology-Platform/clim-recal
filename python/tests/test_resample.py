from pathlib import Path
from typing import Any, Final

import numpy as np
import pytest
from numpy.testing import assert_allclose
from numpy.typing import NDArray
from xarray import open_dataset
from xarray.core.types import T_Dataset

from clim_recal.resample import (
    CPM_CROP_OUTPUT_LOCAL_PATH,
    HADS_CROP_OUTPUT_LOCAL_PATH,
    CPMResampler,
    CPMResamplerManager,
    HADsResampler,
    HADsResamplerManager,
    ResamblerManagerBase,
)
from clim_recal.utils.core import CLI_DATE_FORMAT_STR
from clim_recal.utils.data import RegionOptions, RunOptions
from clim_recal.utils.xarray import (
    FINAL_CONVERTED_CPM_WIDTH,
    FINAL_RESAMPLE_LON_COL,
    plot_xarray,
)

from .utils import (
    CPM_TASMAX_DAY_SERVER_PATH,
    CPM_TASMAX_LOCAL_TEST_PATH,
    FINAL_CPM_DEC_10_X_2_Y_200_210,
    HADS_UK_TASMAX_DAY_SERVER_PATH,
    HADS_UK_TASMAX_LOCAL_TEST_PATH,
)

HADS_FIRST_DATES: Final[NDArray] = np.array(
    ["19800101", "19800102", "19800103", "19800104", "19800105"]
)

# FINAL_CONVERTED_CPM_WIDTH: Final[int] = 410
# FINAL_CONVERTED_CPM_HEIGHT: Final[int] = 660
# FINAL_CONVERTED_CPM_WIDTH: Final[int] = 493
# FINAL_CONVERTED_CPM_HEIGHT: Final[int] = 607
#
# FINAL_CONVERTED_HADS_WIDTH: Final[int] = 410
# FINAL_CONVERTED_HADS_HEIGHT: Final[int] = 660

# RAW_CPM_TASMAX_1980_FIRST_5: Final[NDArray] = np.array(
#     [12.654932, 12.63711, 12.616358, 12.594385, 12.565821], dtype="float32"
# )
# RAW_CPM_TASMAX_1980_DEC_30_FIRST_5: Final[NDArray] = np.array(
#     [13.832666, 13.802149, 13.788477, 13.777491, 13.768946], dtype="float32"
# )


# FINAL_HADS_JAN_10_430_X_230_250_Y: Final[NDArray] = np.array(
#     (
#         np.nan,
#         np.nan,
#         np.nan,
#         np.nan,
#         np.nan,
#         np.nan,
#         np.nan,
#         np.nan,
#         np.nan,
#         np.nan,
#         np.nan,
#         3.61614943,
#         3.22494448,
#         2.87045363,
#         2.62269053,
#         2.79705005,
#         2.73883926,
#         2.48555346,
#         2.46462528,
#         2.61303118,
#     )
# )

# FINAL_HADS_JAN_10_430_X_200_210_Y: Final[NDArray] = np.array(
#     (
#         np.nan,
#         np.nan,
#         np.nan,
#         np.nan,
#         7.57977839,
#         7.47138044,
#         7.27587694,
#         7.27587694,
#         7.07294578,
#         7.04533059,
#     )
# )
#

# FINAL_CPM_DEC_10_X_2_Y_200_210: Final[NDArray] = np.array(
#     (
#         np.nan,
#         np.nan,
#         9.637598,
#         9.646631,
#         9.636621,
#         9.622217,
#         9.625147,
#         9.640039,
#         9.6349125,
#         9.509668,
#     )
# )
#

# @pytest.fixture(scope="session")
# def reference_final_coord_grid() -> T_Dataset:
#     return open_dataset(DEFAULT_RELATIVE_GRID_DATA_PATH, decode_coords="all")


@pytest.fixture
def cpm_tasmax_raw_mount_path(data_mount_path: Path) -> Path:
    return data_mount_path / CPM_TASMAX_DAY_SERVER_PATH


#
# @pytest.fixture
# def cpm_tasmax_raw_5_years_paths(cpm_tasmax_raw_path: Path) -> tuple[Path, ...]:
#     """Return a `tuple` of valid paths for 5 years of"""
#     return tuple(annual_data_paths_generator(parent_path=cpm_tasmax_raw_path))


@pytest.fixture
def hads_tasmax_raw_mount_path(data_mount_path: Path) -> Path:
    return data_mount_path / HADS_UK_TASMAX_DAY_SERVER_PATH


@pytest.fixture
def hads_tasmax_local_test_path(data_fixtures_path: Path) -> Path:
    return data_fixtures_path / HADS_UK_TASMAX_LOCAL_TEST_PATH


@pytest.fixture
def cpm_tasmax_local_test_path(data_fixtures_path: Path) -> Path:
    return data_fixtures_path / CPM_TASMAX_LOCAL_TEST_PATH


# def test_leap_year_days() -> None:
#     """Test covering a leap year of 366 days."""
#     start_date_str: str = "2024-03-01"
#     end_date_str: str = "2025-03-01"
#     xarray_2024_2025: T_DataArray = xarray_example(
#         start_date=start_date_str,
#         end_date=end_date_str,
#         inclusive=True,
#     )
#     assert len(xarray_2024_2025) == year_days_count(leap_years=1)
#
#
# # This is roughly what I had in mind for
# # https://github.com/alan-turing-institute/clim-recal/issues/132
# # This tests converting from a standard calendar to a 360_day calendar.
# @pytest.mark.parametrize(
#     # Only one of start_date and end_date are included the day counts
#     "start_date, end_date, gen_date_count, days_360, converted_days, align_on",
#     [
#         pytest.param(
#             # 4 years, including a leap year
#             "2024-03-02",
#             "2028-03-02",
#             year_days_count(standard_years=3, leap_years=1),
#             year_days_count(xarray_360_day_years=4),
#             year_days_count(standard_years=3, leap_years=1),
#             "year",
#             id="years_4_annual_align",
#         ),
#         pytest.param(
#             # A whole year, most of which is in a leap year, but avoids the leap day
#             "2024-03-02",
#             "2025-03-02",
#             year_days_count(standard_years=1),
#             year_days_count(xarray_360_day_years=1) - 1,
#             year_days_count(standard_years=1),
#             "year",
#             id="leap_year_but_no_leap_day_annual_align",
#         ),
#         pytest.param(
#             # A whole year, the same date range as the previous test,
#             # but includes the leap day and the majority of the days are in a non-leap year
#             # Note: the current final export configuration *adds* a day
#             "2023-03-02",
#             "2024-03-02",
#             year_days_count(leap_years=1),
#             year_days_count(xarray_360_day_years=1) + 1,
#             year_days_count(leap_years=1) + 1,
#             "year",
#             id="leap_year_with_leap_day_annual_align",
#         ),
#         pytest.param(
#             # An exact calendar year which *IS NOT* a leap year
#             "2023-01-01",
#             "2024-01-01",
#             year_days_count(standard_years=1),
#             year_days_count(xarray_360_day_years=1),
#             year_days_count(standard_years=1),
#             "year",
#             id="non_leap_year_annual_align",
#         ),
#         pytest.param(
#             # A leap day (just the days either side, in a leap year)
#             "2024-02-28",
#             "2024-03-01",
#             2,
#             2,
#             2,
#             "year",
#             id="leap_day",
#         ),
#         pytest.param(
#             # A non-leap day (just the days either side, in a non-leap year)
#             "2023-02-28",
#             "2023-03-01",
#             1,
#             1,
#             1,
#             "year",
#             id="non_leap_day_date_align",
#         ),
#         # Add more test cases to cover the different scenarios and edge cases
#         pytest.param(
#             # 4 years, including a leap year
#             # WARNING: the intermittent year days seems a week short
#             "2024-03-02",
#             "2028-03-02",
#             year_days_count(standard_years=3, leap_years=1),
#             year_days_count(xarray_360_day_years=4) - 7,
#             year_days_count(standard_years=3, leap_years=1),
#             "date",
#             id="years_4_date_align",
#             marks=pytest.mark.xfail(reason="raises `date_range_like` error"),
#         ),
#         pytest.param(
#             # A whole year, most of which is in a leap year, but avoids the leap day
#             "2024-03-02",
#             "2025-03-02",
#             year_days_count(standard_years=1),
#             year_days_count(xarray_360_day_years=1) - 2,
#             year_days_count(standard_years=1),
#             "date",
#             id="leap_year_but_no_leap_day_date_align",
#             marks=pytest.mark.xfail(reason="raises `date_range_like` error"),
#         ),
#         pytest.param(
#             # A whole year, the same date range as the previous test,
#             # but includes the leap day and the majority of the days are in a non-leap year
#             # Note: the current final export configuration *adds* a day
#             "2023-03-02",
#             "2024-03-02",
#             year_days_count(leap_years=1),
#             year_days_count(xarray_360_day_years=1) - 1,
#             year_days_count(leap_years=1) + 1,
#             "date",
#             id="leap_year_with_leap_day_date_align",
#             marks=pytest.mark.xfail(reason="raises `date_range_like` error"),
#         ),
#         pytest.param(
#             # An exact calendar year which *IS NOT* a leap year
#             "2023-01-01",
#             "2024-01-01",
#             year_days_count(standard_years=1),
#             year_days_count(xarray_360_day_years=1) - 2,
#             year_days_count(standard_years=1),
#             "date",
#             id="non_leap_year_date_align",
#             marks=pytest.mark.xfail(reason="raises `date_range_like` error"),
#         ),
#         pytest.param(
#             # A leap day (just the days either side, in a leap year)
#             "2024-02-28",
#             "2024-03-01",
#             2,
#             2,
#             2,
#             "date",
#             id="leap_day",
#         ),
#         pytest.param(
#             # A non-leap day (just the days either side, in a non-leap year)
#             "2023-02-28",
#             "2023-03-01",
#             1,
#             1,
#             1,
#             "date",
#             id="non_leap_day_date_align",
#         ),
#     ],
# )
# def test_time_gaps_360_to_standard_calendar(
#     start_date: DateType,
#     end_date: DateType,
#     gen_date_count: int,
#     days_360: int,
#     converted_days: int,
#     align_on: ConvertCalendarAlignOptions,
# ):
#     """Test `convert_xr_calendar` call of `360_day` `DataArray` to `standard` calendar."""
#     # Potential paramaterized variables
#     inclusive_date_range: bool = False  # includes the last day specified
#     use_cftime: bool = True  # Whether to enforece using `cftime` over `datetime64`
#     # align_on: ConvertCalendarAlignOptions = 'date'
#
#     # Create a base
#     base: T_Dataset = xarray_example(
#         start_date, end_date, as_dataset=True, inclusive=inclusive_date_range
#     )
#
#     # Ensure the generated date range matches for later checks
#     # This occurs for a sigle leap year
#     assert len(base.time) == gen_date_count
#
#     # Convert to `360_day` calendar example
#     dates_360: T_Dataset = base.convert_calendar(
#         calendar="360_day",
#         align_on=align_on,
#         use_cftime=use_cftime,
#     )
#
#     # Check the total number of days are as expected
#     assert len(dates_360.time) == days_360
#
#     if converted_days < 5:
#         with pytest.raises(ValueError):
#             convert_xr_calendar(dates_360, align_on=align_on, use_cftime=use_cftime)
#     else:
#         dates_converted: T_Dataset = convert_xr_calendar(
#             dates_360, align_on=align_on, use_cftime=use_cftime
#         )
#         assert len(dates_converted.time) == converted_days
#
#         # Optionally now check which dates have been dropped and added
#         # Add more assertions here...
#         assert all(base.time == dates_converted.time)
#         assert all(base.time != dates_360.time)
#

# @pytest.mark.slow
# @pytest.mark.mount
# @pytest.mark.parametrize("interpolate_na", (True, False))
# def test_convert_cpm_calendar(interpolate_na: bool) -> None:
#     """Test `convert_calendar` on mounted `cpm` data.
#
#     Notes
#     -----
#     If `interpolate_na` is `True`, there shouldn't be `tasmax` `nan` values, hence
#     creating the `na_values` `bool` as the inverse of `interpolate_na`.
#     """
#     any_na_values_in_tasmax: bool = not interpolate_na
#     raw_nc: T_Dataset = open_dataset(
#         CPM_RAW_TASMAX_EXAMPLE_PATH, decode_coords="all", engine=NETCDF4_XARRAY_ENGINE
#     )
#     assert len(raw_nc.time) == 360
#     assert len(raw_nc.time_bnds) == 360
#     converted: T_Dataset = convert_xr_calendar(raw_nc, interpolate_na=interpolate_na)
#     assert len(converted.time) == 365
#     assert len(converted.time_bnds) == 365
#     assert (
#         np.isnan(converted.tasmax.head()[0][0][0].values).all()
#         == any_na_values_in_tasmax
#     )


# @pytest.mark.localcache
# @pytest.mark.mount
# @pytest.mark.slow
# @pytest.mark.parametrize("include_bnds_index", (True, False))
# def test_cpm_xarray_to_standard_calendar(
#     tasmax_cpm_1980_raw: T_Dataset,
#     include_bnds_index: bool,
# ) -> None:
#     """Test 360 raw to 365/366 calendar conversion.
#
#     Notes
#     -----
#     Indexing differs between `include_bnds_index` ``bool`.
#     ```
#     """
#     CORRECT_PROJ4: Final[str] = (
#         "+proj=ob_tran +o_proj=longlat +o_lon_p=0 +o_lat_p=37.5 +lon_0=357.5 +R=6371229 +no_defs=True"
#     )
#     test_converted = cpm_xarray_to_standard_calendar(
#         tasmax_cpm_1980_raw, include_bnds_index=include_bnds_index
#     )
#     assert test_converted.rio.width == CALENDAR_CONVERTED_CPM_WIDTH
#     assert test_converted.rio.height == CALENDAR_CONVERTED_CPM_HEIGHT
#     assert test_converted.rio.crs.to_proj4() == CORRECT_PROJ4
#     assert test_converted.tasmax.rio.crs.to_proj4() == CORRECT_PROJ4
#     assert len(test_converted.time) == 365
#
#     tasmax_data_subset: NDArray
#     if include_bnds_index:
#         assert len(test_converted.tasmax.data) == 2  # second band
#         assert len(test_converted.tasmax.data[0][0]) == 365  # first band
#         assert len(test_converted.tasmax.data[1][0]) == 365  # second band
#         tasmax_data_subset = test_converted.tasmax.data[0][0]  # first band
#     else:
#         assert len(test_converted.tasmax.data) == 1  # no band index
#         tasmax_data_subset = test_converted.tasmax.data[0]
#     assert len(tasmax_data_subset) == 365
#
#     # By default December 1 in a 360 to 365 projection would
#     # be null. The values matching below should indicate the
#     # projection has interpolated null values on the first date
#     assert (
#         tasmax_data_subset[0][0][:5]
#         == PROJECTED_CPM_TASMAX_1980_FIRST_5
#         # test_converted.tasmax.data[0][0][0][0][:5] == PROJECTED_CPM_TASMAX_1980_FIRST_5
#     ).all()
#     # Check December 31 1980, which wouldn't be included in 360 day calendar
#     assert (
#         # test_converted.tasmax.data[0][0][31][0][:5]
#         tasmax_data_subset[31][0][:5]
#         == PROJECTED_CPM_TASMAX_1980_DEC_31_FIRST_5
#     ).all()


# @pytest.mark.localcache
# @pytest.mark.mount
# @pytest.mark.slow
# def test_cpm_reproject_with_standard_calendar(
#     tasmax_cpm_1980_raw_path: Path,
#     test_runs_output_path: Path,
#     variable_name: str = "tasmax",
# ) -> None:
#     """Test all steps around calendar and warping CPM RAW data."""
#     output_path: Path = results_path(
#         "test-cpm-warp",
#         path=test_runs_output_path,
#         mkdir=True,
#         extension=NETCDF_EXTENSION_STR,
#     )
#     plot_path: Path = output_path.parent / (output_path.stem + ".png")
#     projected: T_Dataset = cpm_reproject_with_standard_calendar(
#         tasmax_cpm_1980_raw_path,
#     )
#     assert projected.rio.crs == BRITISH_NATIONAL_GRID_EPSG
#     projected.to_netcdf(output_path)
#     results: T_Dataset = open_dataset(output_path, decode_coords="all")
#     assert (results.time == projected.time).all()
#     assert results.dims == {
#         FINAL_RESAMPLE_LON_COL: FINAL_CONVERTED_CPM_WIDTH,
#         FINAL_RESAMPLE_LAT_COL: FINAL_CONVERTED_CPM_HEIGHT,
#         "time": 365,
#     }
#     assert results.rio.crs == BRITISH_NATIONAL_GRID_EPSG
#     assert len(results.data_vars) == 1
#     assert_allclose(
#         results[variable_name][10][2][200:210], FINAL_CPM_DEC_10_X_2_Y_200_210
#     )
#     plot_xarray(results.tasmax[0], plot_path, time_stamp=True)
#
#
# @pytest.mark.xfail(reason="test not complete")
# def test_cpm_tif_to_standard_calendar(
#     glasgow_example_cropped_cpm_rainfall_path: Path,
# ) -> None:
#     test_converted: tuple[date, ...] = tuple(
#         date_range_generator(
#             *file_name_to_start_end_dates(glasgow_example_cropped_cpm_rainfall_path)
#         )
#     )
#     assert len(test_converted) == 366
#     assert False
#
#
# # @pytest.mark.xfail(reason="not finished writing, will need refactor")
# @pytest.mark.localcache
# @pytest.mark.slow
# @pytest.mark.mount
# @pytest.mark.parametrize("region", ("Glasgow", "Manchester", "London", "Scotland"))
# @pytest.mark.parametrize("data_type", (UKCPLocalProjections, HadUKGrid))
# @pytest.mark.parametrize(
#     # "config", ("direct", "range", "direct_provided", "range_provided")
#     "config",
#     ("direct", "range"),
# )
# def test_crop_xarray(
#     tasmax_cpm_1980_raw_path,
#     tasmax_hads_1980_raw_path,
#     resample_test_cpm_output_path,
#     resample_test_hads_output_path,
#     config: str,
#     data_type: str,
#     region: str,
# ):
#     """Test `cropping` `DataArray` to `standard` calendar."""
#     CPM_FIRST_DATES: np.array = np.array(
#         ["19801201", "19801202", "19801203", "19801204", "19801205"]
#     )
#     test_config: CPMResampler | HADsResampler
#     if data_type == HadUKGrid:
#         output_path: Path = resample_test_hads_output_path / config
#         crop_path: Path = (
#             resample_test_hads_output_path / config / HADS_CROP_OUTPUT_LOCAL_PATH
#         )
#
#         test_config = HADsResampler(
#             input_path=tasmax_hads_1980_raw_path.parent,
#             output_path=output_path,
#             crop_path=crop_path,
#         )
#     else:
#         assert data_type == UKCPLocalProjections
#         output_path: Path = resample_test_cpm_output_path / config
#         crop_path: Path = (
#             resample_test_cpm_output_path / config / CPM_CROP_OUTPUT_LOCAL_PATH
#         )
#         test_config = CPMResampler(
#             input_path=tasmax_cpm_1980_raw_path.parent,
#             output_path=output_path,
#             crop_path=crop_path,
#         )
#     paths: list[Path]
#     try:
#         reproject_result: GDALDataset = test_config.to_reprojection()
#     except FileExistsError:
#         test_config._sync_reprojected_paths(overwrite_output_path=output_path)
#
#     match config:
#         case "direct":
#             paths = [test_config.crop_projection(region=region)]
#         case "range":
#             paths = test_config.range_crop_projection(stop=1)
#         # case "direct_provided":
#         #     paths = [
#         #         test_config.to_reprojection(index=0, source_to_index=tuple(test_config))
#         #     ]
#         # case "range_provided":
#         #     paths = test_config.range_to_reprojection(
#         #         stop=1, source_to_index=tuple(test_config)
#         #     )
#     crop: T_Dataset = open_dataset(paths[0])
#     # assert crop.dims[FINAL_RESAMPLE_LON_COL] == FINAL_CONVERTED_CPM_WIDTH
#     # assert_allclose(export.tasmax[10][5][:10].values, FINAL_CPM_DEC_10_5_X_0_10_Y)
#     if data_type == UKCPLocalProjections:
#         assert crop.dims["time"] == 365
#         assert (
#             CPM_FIRST_DATES == crop.time.dt.strftime(CLI_DATE_FORMAT_STR).head().values
#         ).all()
#     plot_xarray(
#         crop.tasmax[0],
#         path=crop_path / region / f"config-{config}.png",
#         time_stamp=True,
#     )


@pytest.mark.localcache
@pytest.mark.slow
@pytest.mark.mount
@pytest.mark.parametrize(
    "config", ("direct", "range", "direct_provided", "range_provided")
)
def test_cpm_manager(
    resample_test_cpm_output_path, config: str, tasmax_cpm_1980_raw_path: Path
) -> None:
    """Test running default CPM calendar fix."""
    CPM_FIRST_DATES: np.array = np.array(
        ["19801201", "19801202", "19801203", "19801204", "19801205"]
    )
    output_path: Path = resample_test_cpm_output_path / config
    test_config = CPMResampler(
        input_path=tasmax_cpm_1980_raw_path.parent,
        output_path=output_path,
    )
    paths: list[Path]
    match config:
        case "direct":
            paths = [test_config.to_reprojection()]
        case "range":
            paths = test_config.range_to_reprojection(stop=1)
        case "direct_provided":
            paths = [
                test_config.to_reprojection(index=0, source_to_index=tuple(test_config))
            ]
        case "range_provided":
            paths = test_config.range_to_reprojection(
                stop=1, source_to_index=tuple(test_config)
            )
    export: T_Dataset = open_dataset(paths[0])
    assert export.dims["time"] == 365
    assert export.dims[FINAL_RESAMPLE_LON_COL] == FINAL_CONVERTED_CPM_WIDTH
    assert_allclose(export.tasmax[10][5][:10].values, FINAL_CPM_DEC_10_X_2_Y_200_210)
    assert (
        CPM_FIRST_DATES == export.time.dt.strftime(CLI_DATE_FORMAT_STR).head().values
    ).all()
    plot_xarray(
        export.tasmax[0],
        path=resample_test_cpm_output_path / f"config-{config}.png",
        time_stamp=True,
    )


# @pytest.mark.xfail(reason="checking `export.tasmax` values currently yields `nan`")
@pytest.mark.localcache
@pytest.mark.slow
@pytest.mark.mount
@pytest.mark.parametrize("range", (False, True))
def test_hads_manager(
    resample_test_hads_output_path, range: bool, tasmax_hads_1980_raw_path: Path
) -> None:
    """Test running default HADs spatial projection."""
    test_config = HADsResampler(
        input_path=tasmax_hads_1980_raw_path.parent,
        output_path=resample_test_hads_output_path / f"range-{range}",
    )
    paths: list[Path]
    if range:
        paths = test_config.range_to_reprojection(stop=1)
    else:
        paths = [test_config.to_reprojection()]
    export: T_Dataset = open_dataset(paths[0])
    assert len(export.time) == 31
    assert not np.isnan(export.tasmax[0][200:300].values).all()
    assert (
        HADS_FIRST_DATES.astype(object)
        == export.time.dt.strftime(CLI_DATE_FORMAT_STR).head().values
    ).all()
    plot_xarray(
        export.tasmax[0],
        path=resample_test_hads_output_path / f"range-{range}.png",
        time_stamp=True,
    )


# @pytest.mark.localcache
# @pytest.mark.mount
# @pytest.mark.slow
# @pytest.mark.parametrize("data_type", ("hads", "cpm"))
# @pytest.mark.parametrize("use_reference_grid", (True, False))
# def test_interpolate_coords(
#     data_type: str,
#     reference_final_coord_grid: T_Dataset,
#     tasmax_cpm_1980_raw: T_Dataset,
#     tasmax_hads_1980_raw: T_Dataset,
#     use_reference_grid: bool,
# ) -> None:
#     """Test reprojecting raw spatial files.
#
#     Notes
#     -----
#     Still seems to run even when `-m "not mount"` is specified.
#     """
#     reprojected_xr_time_series: T_Dataset
#     kwargs: dict[str, Any] = dict(
#         variable_name="tasmax",
#         x_grid=reference_final_coord_grid.projection_x_coordinate.values,
#         y_grid=reference_final_coord_grid.projection_y_coordinate.values,
#     )
#     x_col_name: str = HADS_XDIM
#     y_col_name: str = HADS_YDIM
#     if data_type == "hads":
#         reprojected_xr_time_series = interpolate_coords(
#             tasmax_hads_1980_raw,
#             x_coord_column_name=x_col_name,
#             y_coord_column_name=y_col_name,
#             use_reference_grid=use_reference_grid,
#             **kwargs,
#         )
#         assert reprojected_xr_time_series.dims["time"] == 31
#         assert_allclose(
#             reprojected_xr_time_series.tasmax[10][430][200:210],
#             FINAL_HADS_JAN_10_430_X_200_210_Y,
#         )
#         if use_reference_grid:
#             assert reprojected_xr_time_series.rio.crs == BRITISH_NATIONAL_GRID_EPSG
#         else:
#             assert reprojected_xr_time_series.rio.crs == tasmax_hads_1980_raw.rio.crs
#     else:
#         x_col_name = CPRUK_XDIM
#         y_col_name = CPRUK_YDIM
#         # We are now using gdal_warp_wrapper. See test_cpm_warp_steps
#         reprojected_xr_time_series = interpolate_coords(
#             tasmax_cpm_1980_raw,
#             x_coord_column_name=x_col_name,
#             y_coord_column_name=y_col_name,
#             use_reference_grid=use_reference_grid,
#             **kwargs,
#         )
#         # Note: this test is to a raw file without 365 day projection
#         assert reprojected_xr_time_series.dims["time"] == 360
#         assert np.isnan(reprojected_xr_time_series.tasmax[0][10][5][:10].values).all()
#         if use_reference_grid:
#             assert reprojected_xr_time_series.rio.crs == BRITISH_NATIONAL_GRID_EPSG
#         else:
#             assert reprojected_xr_time_series.rio.crs == tasmax_cpm_1980_raw.rio.crs
#     assert reprojected_xr_time_series.dims[x_col_name] == 528
#     assert reprojected_xr_time_series.dims[y_col_name] == 651


# @pytest.mark.slow
# @pytest.mark.localcache
# @pytest.mark.mount
# def test_hads_resample_and_reproject(
#     tasmax_hads_1980_raw: T_Dataset,
#     tasmax_cpm_1980_raw: T_Dataset,
# ) -> None:
#     variable_name: str = "tasmax"
#     output_path: Path = Path("tests/runs/reample-hads")
#     # First index is for month, in this case January 1980
#     # The following could be replaced by a cached fixture
#     cpm_to_match: T_Dataset = cpm_reproject_with_standard_calendar(tasmax_cpm_1980_raw)
#     plot_xarray(
#         tasmax_hads_1980_raw.tasmax[0],
#         path=output_path / "tasmas-1980-JAN-1-raw.png",
#         time_stamp=True,
#     )
#
#     assert tasmax_hads_1980_raw.dims["time"] == 31
#     assert tasmax_hads_1980_raw.dims[HADS_RAW_X_COLUMN_NAME] == 900
#     assert tasmax_hads_1980_raw.dims[HADS_RAW_Y_COLUMN_NAME] == 1450
#     reprojected: T_Dataset = hads_resample_and_reproject(
#         tasmax_hads_1980_raw,
#         variable_name=variable_name,
#         cpm_to_match=tasmax_cpm_1980_raw,
#     )
#
#     assert reprojected.rio.crs.to_epsg() == int(BRITISH_NATIONAL_GRID_EPSG[5:])
#     export_netcdf_path: Path = results_path(
#         "tasmax-1980-converted", path=output_path, extension="nc"
#     )
#     reprojected.to_netcdf(export_netcdf_path)
#     read_from_export: T_Dataset = open_dataset(export_netcdf_path, decode_coords="all")
#     plot_xarray(
#         read_from_export.tasmax[0],
#         path=output_path / "tasmax-1980-JAN-1-resampled.png",
#         time_stamp=True,
#     )
#     assert_allclose(
#         read_from_export.tasmax[10][430][200:210], FINAL_HADS_JAN_10_430_X_200_210_Y
#     )
#     assert read_from_export.dims["time"] == 31
#     assert (
#         read_from_export.dims[FINAL_RESAMPLE_LON_COL] == FINAL_CONVERTED_CPM_WIDTH
#     )  # replaces projection_x_coordinate
#     assert (
#         read_from_export.dims[FINAL_RESAMPLE_LAT_COL] == FINAL_CONVERTED_CPM_HEIGHT
#     )  # replaces projection_y_coordinate
#     assert reprojected.rio.crs == read_from_export.rio.crs == BRITISH_NATIONAL_GRID_EPSG
#     # Check projection coordinates match for CPM and HADs
#     assert (
#         reprojected.tasmax.rio.crs
#         == read_from_export.tasmax.rio.crs
#         == BRITISH_NATIONAL_GRID_EPSG
#     )
#     # Check projection coordinates are set at the variable level
#     assert all(cpm_to_match.x == read_from_export.x)
#     assert all(cpm_to_match.y == read_from_export.y)
#     assert (
#         read_from_export.spatial_ref.attrs["spatial_ref"]
#         == cpm_to_match.spatial_ref.attrs["spatial_ref"]
#     )


@pytest.mark.localcache
@pytest.mark.mount
@pytest.mark.parametrize("strict_fail_bool", (True, False))
@pytest.mark.parametrize("manager", (HADsResamplerManager, CPMResamplerManager))
def test_variable_in_base_import_path_error(
    strict_fail_bool: bool,
    manager: HADsResamplerManager | CPMResamplerManager,
    tasmax_hads_1980_raw_path: Path,
) -> None:
    """Test checking import path validity for a given variable."""
    with pytest.raises(manager.VarirableInBaseImportPathError):
        manager(
            input_paths=tasmax_hads_1980_raw_path,
            stop_index=1,
        )
    if strict_fail_bool:
        with pytest.raises(FileExistsError):
            manager(
                input_paths=tasmax_hads_1980_raw_path,
                stop_index=1,
                _strict_fail_if_var_in_input_path=False,
            )


@pytest.mark.localcache
@pytest.mark.slow
@pytest.mark.mount
@pytest.mark.parametrize("multiprocess", (False, True))
def test_execute_resample_configs(
    multiprocess: bool, tmp_path, tasmax_hads_1980_raw_path: Path
) -> None:
    """Test running default HADs spatial projection."""
    test_config = HADsResamplerManager(
        input_paths=tasmax_hads_1980_raw_path.parent,
        resample_paths=tmp_path,
        crop_paths=tmp_path,
        stop_index=1,
    )
    resamplers: tuple[HADsResampler | CPMResampler, ...] = (
        test_config.execute_resample_configs(multiprocess=multiprocess)
    )
    export: T_Dataset = open_dataset(resamplers[0][0])
    assert len(export.time) == 31
    assert not np.isnan(export.tasmax[0][200:300].values).all()
    assert (
        HADS_FIRST_DATES.astype(object)
        == export.time.dt.strftime(CLI_DATE_FORMAT_STR).head().values
    ).all()


#
# @pytest.mark.localcache
# @pytest.mark.slow
# @pytest.mark.mount
# @pytest.mark.parametrize("skip_reproject", (True, False))
# def test_set_cpm_for_coord_alignment(
#     skip_reproject: bool,
#     tasmax_cpm_1980_raw_path: Path,
#     tasmax_cpm_1980_converted_path: Path,
# ) -> None:
#     """Test using `set_cpm_for_coord_alignment` to manage coord alignment."""
#     path: Path = tasmax_cpm_1980_converted_path if skip_reproject else tasmax_cpm_1980_raw_path
#     assert False
#     test_result: T_Dataset = set_cpm_for_coord_alignment(path, skip_reproject)
#     assert isinstance(test_result, Dataset)


@pytest.mark.localcache
@pytest.mark.slow
@pytest.mark.mount
@pytest.mark.parametrize("manager", (CPMResamplerManager, HADsResamplerManager))
# @pytest.mark.parametrize("multiprocess", (False, True))
# @pytest.mark.parametrize("multiprocess", (False, False))
def test_execute_crop_configs(
    manager: ResamblerManagerBase,
    # multiprocess: bool,
    tmp_path: Path,
    resample_test_hads_output_path: Path,
    resample_test_cpm_output_path: Path,
    tasmax_hads_1980_raw_path: Path,
    tasmax_cpm_1980_raw_path: Path,
    tasmax_cpm_1980_converted_path: Path,
) -> None:
    """Test running default HADs spatial projection."""
    multiprocess: bool = False
    input_path: Path
    crop_path: Path
    manager_kwargs: dict[str, Any] = {}
    if manager is HADsResamplerManager:
        input_path = tasmax_hads_1980_raw_path.parent
        crop_path = (
            resample_test_hads_output_path / "manage" / HADS_CROP_OUTPUT_LOCAL_PATH
        )
        manager_kwargs["cpm_for_coord_alignment"] = tasmax_cpm_1980_converted_path
        manager_kwargs["cpm_for_coord_alignment_path_converted"] = True
    else:
        input_path = tasmax_cpm_1980_raw_path.parent
        crop_path = (
            resample_test_cpm_output_path / "manage" / CPM_CROP_OUTPUT_LOCAL_PATH
        )
        manager_kwargs["runs"] = (RunOptions.ONE,)
    test_config: ResamblerManagerBase = manager(
        input_paths=input_path,
        resample_paths=tmp_path,
        crop_paths=crop_path,
        stop_index=1,
        _strict_fail_if_var_in_input_path=False,
        **manager_kwargs,
    )
    if isinstance(test_config, HADsResamplerManager):
        test_config.set_cpm_for_coord_alignment = tasmax_cpm_1980_converted_path

    _: tuple[HADsResampler | CPMResampler, ...] = test_config.execute_resample_configs(
        multiprocess=multiprocess
    )
    region_crops: tuple[HADsResampler | CPMResampler, ...] = (
        test_config.execute_crop_configs(multiprocess=multiprocess)
    )
    region_crop_dict: dict[str, tuple[Path, ...]] = {
        crop.crop_region: tuple(Path(crop.crop_path).iterdir()) for crop in region_crops
    }
    assert len(region_crop_dict) == len(region_crops) == len(RegionOptions)
    for region, path in region_crop_dict.items():
        cropped_region: T_Dataset = open_dataset(path[0])
        bbox = RegionOptions.bounding_box(region)
        assert_allclose(cropped_region["x"].max(), bbox.xmax, rtol=0.1)
        assert_allclose(cropped_region["x"].min(), bbox.xmin, rtol=0.1)
        assert_allclose(cropped_region["y"].max(), bbox.ymax, rtol=0.1)
        assert_allclose(cropped_region["y"].min(), bbox.ymin, rtol=0.1)
        if isinstance(test_config, HADsResamplerManager):
            assert len(cropped_region["time"]) == 31
        else:
            assert len(cropped_region["time"]) == 365
