from unittest.mock import MagicMock, Mock

from screfinery.schema import MiningSessionPayoutSummary, \
    MiningSessionPayoutItem, Related, MiningSessionPayoutUser
from screfinery.stores.mining_session_store import calc_payout_summary
from screfinery.stores.model import MiningSession, MiningSessionEntry, User


def with_attrs(obj, attrs):
    for k, v in attrs.items():
        setattr(obj, k, v)
    return obj


def mock_user(**kwargs):
    return with_attrs(Mock(spec=User), kwargs)


def mock_mining_session(**kwargs):
    return with_attrs(Mock(spec=MiningSession), kwargs)


def mock_mining_session_entry(**kwargs):
    return with_attrs(Mock(spec=MiningSessionEntry), kwargs)


def test_payout_summary_without_entries():
    ms = mock_mining_session(entries=[])
    result = calc_payout_summary(ms)
    assert result == MiningSessionPayoutSummary(
        total_profit=0,
        average_profit=0,
        payouts=[])


def test_payout_summary_with_one_user():
    creator = User(id=1, name="user1")
    ms = mock_mining_session(
        creator=creator,
        users_invited=[],
        entries=[
            mock_mining_session_entry(
                user=creator,
                profit=100,
            ),
            mock_mining_session_entry(
                user=creator,
                profit=100,
            )
        ]
    )
    result = calc_payout_summary(ms)
    assert result == MiningSessionPayoutSummary(
        total_profit=200,
        average_profit=200,
        payouts=[])


def test_payout_summary_2x_users_1x_user_zero_profit():
    creator = User(id=1, name="creator")
    users_invited = [User(id=2, name="user2")]
    ms = mock_mining_session(
        creator=creator,
        users_invited=users_invited,
        entries=[
            mock_mining_session_entry(
                user=creator,
                profit=100,
            ),
            mock_mining_session_entry(
                user=users_invited[0],
                profit=0,
            )
        ]
    )
    result = calc_payout_summary(ms)
    assert result == MiningSessionPayoutSummary(
        total_profit=100,
        average_profit=50,
        payouts=[
            MiningSessionPayoutItem(
                user=Related(id=1, name="creator"),
                recipients=[
                    MiningSessionPayoutUser(user_id=2, user_name="user2", amount=50),
                ]
            )
        ]
    )


def test_payout_summary_2x_users_1x_user_zero_profit_multiple_user1_entries():
    creator = User(id=1, name="creator")
    users_invited = [User(id=2, name="user2")]
    ms = mock_mining_session(
        creator=creator,
        users_invited=users_invited,
        entries=[
            mock_mining_session_entry(
                user=creator,
                profit=100,
            ),
            mock_mining_session_entry(
                user=creator,
                profit=50,
            ),
            mock_mining_session_entry(
                user=users_invited[0],
                profit=0,
            )
        ]
    )
    result = calc_payout_summary(ms)
    assert result == MiningSessionPayoutSummary(
        total_profit=150,
        average_profit=75,
        payouts=[
            MiningSessionPayoutItem(
                user=Related(id=1, name="creator"),
                recipients=[
                    MiningSessionPayoutUser(user_id=2, user_name="user2", amount=75),
                ]
            )
        ]
    )


def test_payout_summary_3x_users_2x_users_zero_profit():
    creator = User(id=1, name="creator")
    users_invited = [User(id=2, name="user2"), User(id=3, name="user3")]
    ms = mock_mining_session(
        creator=creator,
        users_invited=users_invited,
        entries=[
            mock_mining_session_entry(
                user=creator,
                profit=100,
            ),
            mock_mining_session_entry(
                user=users_invited[0],
                profit=0,
            ),
            mock_mining_session_entry(
                user=users_invited[1],
                profit=0,
            )
        ])
    result = calc_payout_summary(ms)
    assert result == MiningSessionPayoutSummary(
        total_profit=100,
        average_profit=33.33,
        payouts=[
            MiningSessionPayoutItem(
                user=Related(id=1, name="creator"),
                recipients=[
                    MiningSessionPayoutUser(user_id=2, user_name="user2", amount=33.33),
                    MiningSessionPayoutUser(user_id=3, user_name="user3", amount=33.33),
                ]
            )
        ]
    )


def test_payout_summary_3x_users_1x_users_zero_profit():
    creator = User(id=1, name="creator")
    users_invited = [
        User(id=2, name="user2"),
        User(id=3, name="user3")
    ]
    ms = mock_mining_session(
        creator=creator,
        users_invited=users_invited,
        entries=[
            mock_mining_session_entry(
                user=creator,
                profit=150,
            ),
            mock_mining_session_entry(
                user=users_invited[0],
                profit=50,
            ),
            mock_mining_session_entry(
                user=users_invited[1],
                profit=0,
            )
        ])
    result = calc_payout_summary(ms)
    assert result == MiningSessionPayoutSummary(
        total_profit=200,
        average_profit=66.67,
        payouts=[
            MiningSessionPayoutItem(
                user=Related(id=1, name="creator"),
                recipients=[
                    MiningSessionPayoutUser(user_id=2, user_name="user2", amount=16.67),
                    MiningSessionPayoutUser(user_id=3, user_name="user3", amount=66.67),
                ]
            )
        ]
    )


def test_payout_summary_3x_users_2x_payout():
    creator = User(id=1, name="creator")
    users_invited = [
        User(id=2, name="user2"),
        User(id=3, name="user3")
    ]
    ms = mock_mining_session(
        creator=creator,
        users_invited=users_invited,
        entries=[
            mock_mining_session_entry(
                user=creator,
                profit=60,
            ),
            mock_mining_session_entry(
                user=users_invited[0],
                profit=60,
            ),
            mock_mining_session_entry(
                user=users_invited[1],
                profit=0,
            )
        ])
    result = calc_payout_summary(ms)
    assert result == MiningSessionPayoutSummary(
        total_profit=120,
        average_profit=40,
        payouts=[
            MiningSessionPayoutItem(
                user=Related(id=1, name="creator"),
                recipients=[
                    MiningSessionPayoutUser(user_id=3, user_name="user3", amount=20),
                ]
            ),
            MiningSessionPayoutItem(
                user=Related(id=2, name="user2"),
                recipients=[
                    MiningSessionPayoutUser(user_id=3, user_name="user3", amount=20),
                ]
            )
        ]
    )
