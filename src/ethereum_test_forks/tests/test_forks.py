"""Test fork utilities."""

from typing import Dict, cast

import pytest
from pydantic import BaseModel

from ethereum_test_base_types import BlobSchedule

from ..forks.forks import (
    Berlin,
    Cancun,
    Frontier,
    Homestead,
    Istanbul,
    London,
    Osaka,
    Paris,
    Prague,
    Shanghai,
)
from ..forks.transition import (
    BerlinToLondonAt5,
    CancunToPragueAtTime15k,
    ParisToShanghaiAtTime15k,
    PragueToOsakaAtTime15k,
    ShanghaiToCancunAtTime15k,
)
from ..helpers import (
    Fork,
    forks_from,
    forks_from_until,
    get_deployed_forks,
    get_forks,
    transition_fork_from_to,
    transition_fork_to,
)
from ..transition_base_fork import transition_fork

FIRST_DEPLOYED = Frontier
LAST_DEPLOYED = Prague
LAST_DEVELOPMENT = Osaka
DEVELOPMENT_FORKS = [Osaka]


def test_transition_forks():
    """Test transition fork utilities."""
    assert transition_fork_from_to(Berlin, London) == BerlinToLondonAt5
    assert transition_fork_from_to(Berlin, Paris) is None
    assert transition_fork_to(Shanghai) == {ParisToShanghaiAtTime15k}

    # Test forks transitioned to and from
    assert BerlinToLondonAt5.transitions_to() == London
    assert BerlinToLondonAt5.transitions_from() == Berlin

    assert BerlinToLondonAt5.transition_tool_name(4, 0) == "Berlin"
    assert BerlinToLondonAt5.transition_tool_name(5, 0) == "London"
    # Default values of transition forks is the transition block
    assert BerlinToLondonAt5.transition_tool_name() == "London"

    assert ParisToShanghaiAtTime15k.transition_tool_name(0, 14_999) == "Merge"
    assert ParisToShanghaiAtTime15k.transition_tool_name(0, 15_000) == "Shanghai"
    assert ParisToShanghaiAtTime15k.transition_tool_name() == "Shanghai"

    assert BerlinToLondonAt5.header_base_fee_required(4, 0) is False
    assert BerlinToLondonAt5.header_base_fee_required(5, 0) is True

    assert ParisToShanghaiAtTime15k.header_withdrawals_required(0, 14_999) is False
    assert ParisToShanghaiAtTime15k.header_withdrawals_required(0, 15_000) is True

    assert ParisToShanghaiAtTime15k.engine_new_payload_version(0, 14_999) == 1
    assert ParisToShanghaiAtTime15k.engine_new_payload_version(0, 15_000) == 2

    assert BerlinToLondonAt5.fork_at(4, 0) == Berlin
    assert BerlinToLondonAt5.fork_at(5, 0) == London
    assert ParisToShanghaiAtTime15k.fork_at(0, 14_999) == Paris
    assert ParisToShanghaiAtTime15k.fork_at(0, 15_000) == Shanghai
    assert ParisToShanghaiAtTime15k.fork_at() == Paris
    assert ParisToShanghaiAtTime15k.fork_at(10_000_000, 14_999) == Paris


def test_forks_from():  # noqa: D103
    assert forks_from(Paris)[0] == Paris
    assert forks_from(Paris)[-1] == LAST_DEPLOYED
    assert forks_from(Paris, deployed_only=True)[0] == Paris
    assert forks_from(Paris, deployed_only=True)[-1] == LAST_DEPLOYED
    assert forks_from(Paris, deployed_only=False)[0] == Paris
    # assert forks_from(Paris, deployed_only=False)[-1] == LAST_DEVELOPMENT  # Too flaky


def test_forks():
    """Test fork utilities."""
    assert forks_from_until(Berlin, Berlin) == [Berlin]
    assert forks_from_until(Berlin, London) == [Berlin, London]
    assert forks_from_until(Berlin, Paris) == [
        Berlin,
        London,
        Paris,
    ]

    # Test fork names
    assert London.name() == "London"
    assert ParisToShanghaiAtTime15k.name() == "ParisToShanghaiAtTime15k"
    assert f"{London}" == "London"
    assert f"{ParisToShanghaiAtTime15k}" == "ParisToShanghaiAtTime15k"

    # Merge name will be changed to paris, but we need to check the inheriting fork name is still
    # the default
    assert Paris.transition_tool_name() == "Merge"
    assert Shanghai.transition_tool_name() == "Shanghai"
    assert f"{Paris}" == "Paris"
    assert f"{Shanghai}" == "Shanghai"
    assert f"{ParisToShanghaiAtTime15k}" == "ParisToShanghaiAtTime15k"

    # Test some fork properties
    assert Berlin.header_base_fee_required(0, 0) is False
    assert London.header_base_fee_required(0, 0) is True
    assert Paris.header_base_fee_required(0, 0) is True
    # Default values of normal forks if the genesis block
    assert Paris.header_base_fee_required() is True

    # Transition forks too
    assert cast(Fork, BerlinToLondonAt5).header_base_fee_required(4, 0) is False
    assert cast(Fork, BerlinToLondonAt5).header_base_fee_required(5, 0) is True
    assert cast(Fork, ParisToShanghaiAtTime15k).header_withdrawals_required(0, 14_999) is False
    assert cast(Fork, ParisToShanghaiAtTime15k).header_withdrawals_required(0, 15_000) is True
    assert cast(Fork, ParisToShanghaiAtTime15k).header_withdrawals_required() is True


class ForkInPydanticModel(BaseModel):
    """Fork in pydantic model."""

    fork_1: Fork
    fork_2: Fork
    fork_3: Fork | None


def test_fork_in_pydantic_model():
    """Test fork in pydantic model."""
    model = ForkInPydanticModel(fork_1=Paris, fork_2=ParisToShanghaiAtTime15k, fork_3=None)
    assert model.model_dump() == {
        "fork_1": "Paris",
        "fork_2": "ParisToShanghaiAtTime15k",
        "fork_3": None,
    }
    assert (
        model.model_dump_json()
        == '{"fork_1":"Paris","fork_2":"ParisToShanghaiAtTime15k","fork_3":null}'
    )
    model = ForkInPydanticModel.model_validate_json(
        '{"fork_1": "Paris", "fork_2": "ParisToShanghaiAtTime15k", "fork_3": null}'
    )
    assert model.fork_1 == Paris
    assert model.fork_2 == ParisToShanghaiAtTime15k
    assert model.fork_3 is None


def test_fork_comparison():
    """Test fork comparison operators."""
    # Test fork comparison
    assert Paris > Berlin
    assert not Berlin > Paris
    assert Berlin < Paris
    assert not Paris < Berlin

    assert Paris >= Berlin
    assert not Berlin >= Paris
    assert Berlin <= Paris
    assert not Paris <= Berlin

    assert London > Berlin
    assert not Berlin > London
    assert Berlin < London
    assert not London < Berlin

    assert London >= Berlin
    assert not Berlin >= London
    assert Berlin <= London
    assert not London <= Berlin

    assert Berlin >= Berlin
    assert Berlin <= Berlin
    assert not Berlin > Berlin
    assert not Berlin < Berlin

    fork = Berlin
    assert fork >= Berlin
    assert fork <= Berlin
    assert not fork > Berlin
    assert not fork < Berlin
    assert fork == Berlin


def test_transition_fork_comparison():
    """
    Test comparing to a transition fork.

    The comparison logic is based on the logic we use to generate the tests.

    E.g. given transition fork A->B, when filling, and given the from/until markers,
    we expect the following logic:

    Marker    Comparison   A->B Included
    --------- ------------ ---------------
    From A    fork >= A    True
    Until A   fork <= A    False
    From B    fork >= B    True
    Until B   fork <= B    True
    """
    assert BerlinToLondonAt5 >= Berlin
    assert not BerlinToLondonAt5 <= Berlin
    assert BerlinToLondonAt5 >= London
    assert BerlinToLondonAt5 <= London

    # Comparisons between transition forks is done against the `transitions_to` fork
    assert BerlinToLondonAt5 < ParisToShanghaiAtTime15k
    assert ParisToShanghaiAtTime15k > BerlinToLondonAt5
    assert BerlinToLondonAt5 == BerlinToLondonAt5
    assert BerlinToLondonAt5 != ParisToShanghaiAtTime15k
    assert BerlinToLondonAt5 <= ParisToShanghaiAtTime15k
    assert ParisToShanghaiAtTime15k >= BerlinToLondonAt5

    assert sorted(
        {
            PragueToOsakaAtTime15k,
            CancunToPragueAtTime15k,
            ParisToShanghaiAtTime15k,
            ShanghaiToCancunAtTime15k,
            BerlinToLondonAt5,
        }
    ) == [
        BerlinToLondonAt5,
        ParisToShanghaiAtTime15k,
        ShanghaiToCancunAtTime15k,
        CancunToPragueAtTime15k,
        PragueToOsakaAtTime15k,
    ]


def test_get_forks():  # noqa: D103
    all_forks = get_forks()
    assert all_forks[0] == FIRST_DEPLOYED
    # assert all_forks[-1] == LAST_DEVELOPMENT  # Too flaky


def test_deployed_forks():  # noqa: D103
    deployed_forks = get_deployed_forks()
    assert deployed_forks[0] == FIRST_DEPLOYED
    assert deployed_forks[-1] == LAST_DEPLOYED


class PrePreAllocFork(Shanghai):
    """Dummy fork used for testing."""

    @classmethod
    def pre_allocation(cls) -> Dict:
        """Return some starting point for allocation."""
        return {"test": "test"}


class PreAllocFork(PrePreAllocFork):
    """Dummy fork used for testing."""

    @classmethod
    def pre_allocation(cls) -> Dict:
        """Add allocation to the pre-existing one from previous fork."""
        return {"test2": "test2"} | super(PreAllocFork, cls).pre_allocation()


@transition_fork(to_fork=PreAllocFork, at_timestamp=15_000)  # type: ignore
class PreAllocTransitionFork(PrePreAllocFork):
    """PrePreAllocFork to PreAllocFork transition at Timestamp 15k."""

    pass


def test_pre_alloc():  # noqa: D103
    assert PrePreAllocFork.pre_allocation() == {"test": "test"}
    assert PreAllocFork.pre_allocation() == {"test": "test", "test2": "test2"}
    assert PreAllocTransitionFork.pre_allocation() == {
        "test": "test",
        "test2": "test2",
    }
    assert PreAllocTransitionFork.pre_allocation() == {
        "test": "test",
        "test2": "test2",
    }


def test_precompiles():  # noqa: D103
    Cancun.precompiles() == list(range(11))[1:]  # noqa: B015


def test_tx_types():  # noqa: D103
    Cancun.tx_types() == list(range(4))  # noqa: B015


@pytest.mark.parametrize(
    "fork",
    [
        pytest.param(Berlin, id="Berlin"),
        pytest.param(Istanbul, id="Istanbul"),
        pytest.param(Homestead, id="Homestead"),
        pytest.param(Frontier, id="Frontier"),
    ],
)
@pytest.mark.parametrize(
    "calldata",
    [
        pytest.param(b"\0", id="zero-data"),
        pytest.param(b"\1", id="non-zero-data"),
    ],
)
@pytest.mark.parametrize(
    "create_tx",
    [False, True],
)
def test_tx_intrinsic_gas_functions(fork: Fork, calldata: bytes, create_tx: bool):  # noqa: D103
    intrinsic_gas = 21_000
    if calldata == b"\0":
        intrinsic_gas += 4
    else:
        if fork >= Istanbul:
            intrinsic_gas += 16
        else:
            intrinsic_gas += 68

    if create_tx:
        if fork >= Homestead:
            intrinsic_gas += 32000
        intrinsic_gas += 2
    assert (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=calldata,
            contract_creation=create_tx,
        )
        == intrinsic_gas
    )


class FutureFork(Osaka):
    """
    Dummy fork used for testing.

    Contains no changes to the blob parameters from the parent fork in order to confirm that
    it's added to the blob schedule even if it doesn't have any changes.
    """

    pass


@pytest.mark.parametrize(
    "fork,expected_schedule",
    [
        pytest.param(Frontier, None, id="Frontier"),
        pytest.param(
            Cancun,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
            },
            id="Cancun",
        ),
        pytest.param(
            Prague,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
                "Prague": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
            },
            id="Prague",
        ),
        pytest.param(
            Osaka,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
                "Prague": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
                "Osaka": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
            },
            id="Osaka",
        ),
        pytest.param(
            CancunToPragueAtTime15k,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
                "Prague": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
            },
            id="CancunToPragueAtTime15k",
        ),
        pytest.param(
            PragueToOsakaAtTime15k,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
                "Prague": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
                "Osaka": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
            },
            id="PragueToOsakaAtTime15k",
        ),
        pytest.param(
            FutureFork,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
                "Prague": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
                "Osaka": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
                "FutureFork": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
            },
            id="FutureFork",
        ),
    ],
)
def test_blob_schedules(fork: Fork, expected_schedule: Dict | None):
    """Test blob schedules for different forks."""
    if expected_schedule is None:
        assert fork.blob_schedule() is None
    else:
        assert fork.blob_schedule() == BlobSchedule(**expected_schedule)
