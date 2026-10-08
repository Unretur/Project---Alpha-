from __future__ import annotations

import pandas as pd


def align_asof(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_on: str,
    right_on: str,
) -> pd.DataFrame:
    """
    Align each row in the right DataFrame to the latest
    observation available at or before the left timestamp.
    """

    left_sorted = left.sort_values(left_on).copy()
    right_sorted = right.sort_values(right_on).copy()

    aligned = pd.merge_asof(
        left_sorted,
        right_sorted,
        left_on=left_on,
        right_on=right_on,
        direction="backward",
    )

    return aligned


if __name__ == "__main__":

    # Decision timeline
    decisions = pd.DataFrame(
        {
            "decision_time": pd.to_datetime(
                [
                    "2026-10-05 10:00:00",
                    "2026-10-05 10:05:00",
                    "2026-10-05 10:10:00",
                    "2026-10-05 10:15:00",
                ],
                utc=True,
            )
        }
    )

    # Information that became available at different times
    observations = pd.DataFrame(
        {
            "available_time": pd.to_datetime(
                [
                    "2026-10-05 09:58:00",
                    "2026-10-05 10:07:00",
                    "2026-10-05 10:14:00",
                ],
                utc=True,
            ),
            "value": [
                100,
                105,
                110,
            ],
        }
    )

    result = align_asof(
        decisions,
        observations,
        left_on="decision_time",
        right_on="available_time",
    )

    print("Decision timeline:")
    print(decisions)
    print()

    print("Available observations:")
    print(observations)
    print()

    print("Aligned result:")
    print(result)