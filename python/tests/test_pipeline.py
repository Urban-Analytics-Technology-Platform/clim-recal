from pathlib import Path

import pytest

from clim_recal.pipeline import main
from clim_recal.utils.core import (
    CLIMATE_DATA_PATH,
    DARWIN_MOUNT_PATH,
    DEBIAN_MOUNT_PATH,
    climate_data_mount_path,
    is_platform_darwin,
)


def test_climate_data_mount_path() -> None:
    """Test OS specifc mount path."""
    if is_platform_darwin():
        assert climate_data_mount_path() == DARWIN_MOUNT_PATH / CLIMATE_DATA_PATH
    else:
        assert climate_data_mount_path() == DEBIAN_MOUNT_PATH / CLIMATE_DATA_PATH


@pytest.mark.parametrize(
    "execute",
    (
        False,
        pytest.param(
            True,
            marks=(
                pytest.mark.mount,
                pytest.mark.slow,
            ),
        ),
    ),
)
@pytest.mark.parametrize("multiprocess", (True, False))
@pytest.mark.parametrize("variables", (("rainfall",), ("rainfall", "tasmax")))
def test_main(
    execute: bool,
    variables: tuple[str],
    resample_test_runs_output_path: Path,
    multiprocess: bool,
    capsys,
) -> None:
    """Test running pipeline configurations."""
    results = main(
        execute=execute,
        variables=variables,
        output_path=resample_test_runs_output_path,
        skip_hads_spatial_2k_projection=True,
        skip_cpm_standard_calendar_projection=False,
        stop_index=1,
        cpus=2,
        multiprocess=multiprocess,
    )
    captured = capsys.readouterr()
    assert f"variables_count={len(variables)}" in captured.out
    assert results == None
