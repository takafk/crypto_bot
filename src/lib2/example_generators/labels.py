from typing import Tuple, List, Any
import pandas as pd

import prefect
from prefect import task

from .helper import CURRENT


@task(
    checkpoint=True,
    target="labels/{label_pipe.name}/{parameters[universe]}_{start_dt}_{end_dt}.pkl",
    result=CURRENT,
)
def generate_label(
    start_dt: str, end_dt: str, dsmeta: Tuple[str, List[str]], label_pipe: Any
) -> pd.Series:
    """Generate features for each symbols.

    Args:
        dsmeta (Tuple[str, List[str]]): Tuple of datastore and symbols.
        label_pipe (Any): label pipeline defined in lib2.compute_factory

    Returns:
        pd.DataFrame: pd.DataFrame of label.

    Note:
        - We allow many NaNs at this moment. We treat them in creating examples later.
    """
    logger = prefect.context.get("logger")

    logger.info("Start to create labels.")

    # index = timestamp, columns = symbols
    label: pd.DataFrame = label_pipe.compute(dsmeta)

    label = label[(label.index >= start_dt) & (label.index <= end_dt)]

    label = label.stack().sort_index().rename("label")

    symbols = dsmeta[1]

    assert all(
        label.groupby(pd.Grouper(level=0)).count() == len(symbols)
    ), "Several samples do not have enough symbols in day. Change interval to have continuous data."

    logger.info("End of creating labels.")

    return label
