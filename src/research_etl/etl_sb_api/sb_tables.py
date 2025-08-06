from typing import NamedTuple
from typing import Literal


class SBTable(NamedTuple):
    """ "SB API Table details"""

    table_name: str
    table_type: Literal["static", "transaction"]
    part_column: str


validation_taps = SBTable(
    table_name="v_validation_taps",
    table_type="transaction",
    part_column="transactiontimestamp",
)

mainshift = SBTable(
    table_name="v_mainshift",
    table_type="transaction",
    part_column="insertdate",
)

trips = SBTable(
    table_name="v_trips",
    table_type="transaction",
    part_column="transactiontimestamp",
)

sales_txns = SBTable(
    table_name="v_sales_txns",
    table_type="transaction",
    part_column="transactiontimestamp",
)

media = SBTable(
    table_name="v_media",
    table_type="transaction",
    part_column="statuschangetimestamp",
)

shiftevent = SBTable(
    table_name="v_shiftevent",
    table_type="transaction",
    part_column="creadate",
)

person = SBTable(
    table_name="v_person",
    table_type="static",
    part_column="",
)

tvmtable = SBTable(
    table_name="v_tvmtable",
    table_type="static",
    part_column="",
)
