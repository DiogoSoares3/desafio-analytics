"""Acquire the canonical Microsoft AdventureWorks OLTP data and load it into DuckDB Parquet.

Downloads the public ``AdventureWorks-oltp-install-script.zip`` (Microsoft ``sql-server-samples``
release ``adventureworks``), reads the ~14 in-scope tables straight into DuckDB, and writes one
committed ``data/adventure_works/<table>.parquet`` per table -- the offline source-of-record that
``_sources.yml`` points at via ``read_parquet``. No Postgres, no SQL Server, no docker.

Date-shift correction
---------------------
The current Microsoft release date-shifts every ``OrderDate`` forward by a uniform, constant number
of days so the sample always looks "recent" (the first order, id 43659, ships as ~2022-05-30 instead
of its canonical 2011-05-31). The shift preserves the full 1126-day span between the first and last
order, so it is exactly reversible: we subtract that same constant offset to restore the canonical
2011-2014 calendar. The offset is derived from the data (min OrderDate vs the canonical
first-order date), not hard-coded, so the script self-corrects if Microsoft re-shifts the
release. The 2011 gross reconciliation ($12,646,112.16, ADR-0001) is asserted at the end as
the correctness oracle.
"""

from __future__ import annotations

import datetime as dt
import os
import tempfile
import urllib.request
import zipfile
from decimal import Decimal
from pathlib import Path

import duckdb

MS_ZIP_URL = (
    "https://github.com/Microsoft/sql-server-samples/releases/download/"
    "adventureworks/AdventureWorks-oltp-install-script.zip"
)

# Canonical OrderDate of the first sales order (id 43659) in the un-shifted AdventureWorks dataset.
CANONICAL_FIRST_ORDER_DATE = dt.date(2011, 5, 31)
# Canonical first->last OrderDate span (2011-05-31 .. 2014-06-30); guards a uniform shift.
CANONICAL_ORDER_DATE_SPAN_DAYS = 1126
# ADR-0001 audited 2011 gross (all sales) = sum(unitprice * orderqty) over orders dated 2011.
EXPECTED_2011_GROSS = Decimal("12646112.16")

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "data" / "adventure_works"

# Field/row delimiters differ per source CSV: the XML-bearing Person table uses "+|" / "&|\n";
# every other in-scope table uses tab / newline (per the BULK INSERT statements in instawdb.sql).
TAB = "\t"

# Physical column order of each in-scope CSV, taken verbatim from the CREATE TABLE definitions in
# the bundled instawdb.sql (computed columns such as SalesOrderNumber / TotalDue ARE present in the
# CSV, so they are listed here too). Only a subset is projected into the Parquet.
RAW_COLUMNS: dict[str, list[str]] = {
    "salesorderheader": [
        "salesorderid",
        "revisionnumber",
        "orderdate",
        "duedate",
        "shipdate",
        "status",
        "onlineorderflag",
        "salesordernumber",
        "purchaseordernumber",
        "accountnumber",
        "customerid",
        "salespersonid",
        "territoryid",
        "billtoaddressid",
        "shiptoaddressid",
        "shipmethodid",
        "creditcardid",
        "creditcardapprovalcode",
        "currencyrateid",
        "subtotal",
        "taxamt",
        "freight",
        "totaldue",
        "comment",
        "rowguid",
        "modifieddate",
    ],
    "salesorderdetail": [
        "salesorderid",
        "salesorderdetailid",
        "carriertrackingnumber",
        "orderqty",
        "productid",
        "specialofferid",
        "unitprice",
        "unitpricediscount",
        "linetotal",
        "rowguid",
        "modifieddate",
    ],
    "salesorderheadersalesreason": ["salesorderid", "salesreasonid", "modifieddate"],
    "salesreason": ["salesreasonid", "name", "reasontype", "modifieddate"],
    "customer": [
        "customerid",
        "personid",
        "storeid",
        "territoryid",
        "accountnumber",
        "rowguid",
        "modifieddate",
    ],
    "person": [
        "businessentityid",
        "persontype",
        "namestyle",
        "title",
        "firstname",
        "middlename",
        "lastname",
        "suffix",
        "emailpromotion",
        "additionalcontactinfo",
        "demographics",
        "rowguid",
        "modifieddate",
    ],
    "product": [
        "productid",
        "name",
        "productnumber",
        "makeflag",
        "finishedgoodsflag",
        "color",
        "safetystocklevel",
        "reorderpoint",
        "standardcost",
        "listprice",
        "size",
        "sizeunitmeasurecode",
        "weightunitmeasurecode",
        "weight",
        "daystomanufacture",
        "productline",
        "class",
        "style",
        "productsubcategoryid",
        "productmodelid",
        "sellstartdate",
        "sellenddate",
        "discontinueddate",
        "rowguid",
        "modifieddate",
    ],
    "productsubcategory": [
        "productsubcategoryid",
        "productcategoryid",
        "name",
        "rowguid",
        "modifieddate",
    ],
    "productcategory": ["productcategoryid", "name", "rowguid", "modifieddate"],
    "address": [
        "addressid",
        "addressline1",
        "addressline2",
        "city",
        "stateprovinceid",
        "postalcode",
        "spatiallocation",
        "rowguid",
        "modifieddate",
    ],
    "stateprovince": [
        "stateprovinceid",
        "stateprovincecode",
        "countryregioncode",
        "isonlystateprovinceflag",
        "name",
        "territoryid",
        "rowguid",
        "modifieddate",
    ],
    "countryregion": ["countryregioncode", "name", "modifieddate"],
    "creditcard": ["creditcardid", "cardtype", "cardnumber", "expmonth", "expyear", "modifieddate"],
    "store": [
        "businessentityid",
        "name",
        "salespersonid",
        "demographics",
        "rowguid",
        "modifieddate",
    ],
    "specialoffer": [
        "specialofferid",
        "description",
        "discountpct",
        "type",
        "category",
        "startdate",
        "enddate",
        "minqty",
        "maxqty",
        "rowguid",
        "modifieddate",
    ],
}

# Source CSV filename per table (case-sensitive as shipped in the zip).
CSV_FILENAME: dict[str, str] = {
    "salesorderheader": "SalesOrderHeader.csv",
    "salesorderdetail": "SalesOrderDetail.csv",
    "salesorderheadersalesreason": "SalesOrderHeaderSalesReason.csv",
    "salesreason": "SalesReason.csv",
    "customer": "Customer.csv",
    "person": "Person.csv",
    "product": "Product.csv",
    "productsubcategory": "ProductSubcategory.csv",
    "productcategory": "ProductCategory.csv",
    "address": "Address.csv",
    "stateprovince": "StateProvince.csv",
    "countryregion": "CountryRegion.csv",
    "creditcard": "CreditCard.csv",
    "specialoffer": "SpecialOffer.csv",
    "store": "Store.csv",
}

# Projection from the raw all-VARCHAR staging relation to the typed, in-scope Parquet columns.
# Column names here MUST match what the staging models consume (the retired seed schemas).
# ``{offset}`` is substituted with the derived date-shift offset for salesorderheader.orderdate.
PROJECTIONS: dict[str, str] = {
    "salesorderheader": """
        cast(salesorderid as integer) as salesorderid,
        salesordernumber,
        (cast(orderdate as timestamp)::date - interval '{offset}' day)::date as orderdate,
        cast(status as integer) as status,
        onlineorderflag = '1' as onlineorderflag,
        cast(customerid as integer) as customerid,
        cast(nullif(creditcardid, '') as integer) as creditcardid,
        cast(shiptoaddressid as integer) as shiptoaddressid,
        cast(billtoaddressid as integer) as billtoaddressid,
        cast(subtotal as decimal(19, 4)) as subtotal,
        cast(taxamt as decimal(19, 4)) as taxamt,
        cast(freight as decimal(19, 4)) as freight
    """,
    "salesorderdetail": """
        cast(salesorderdetailid as integer) as salesorderdetailid,
        cast(salesorderid as integer) as salesorderid,
        cast(productid as integer) as productid,
        cast(orderqty as integer) as orderqty,
        cast(unitprice as decimal(19, 4)) as unitprice,
        cast(unitpricediscount as decimal(19, 4)) as unitpricediscount,
        cast(linetotal as decimal(38, 6)) as linetotal,
        cast(specialofferid as integer) as specialofferid
    """,
    "salesorderheadersalesreason": """
        cast(salesorderid as integer) as salesorderid,
        cast(salesreasonid as integer) as salesreasonid
    """,
    "salesreason": """
        cast(salesreasonid as integer) as salesreasonid,
        name,
        reasontype
    """,
    "customer": """
        cast(customerid as integer) as customerid,
        cast(nullif(personid, '') as integer) as personid,
        cast(nullif(storeid, '') as integer) as storeid,
        cast(nullif(territoryid, '') as integer) as territoryid
    """,
    "person": """
        cast(businessentityid as integer) as businessentityid,
        firstname,
        lastname,
        persontype
    """,
    "product": """
        cast(productid as integer) as productid,
        name,
        productnumber,
        cast(nullif(productsubcategoryid, '') as integer) as productsubcategoryid
    """,
    "productsubcategory": """
        cast(productsubcategoryid as integer) as productsubcategoryid,
        cast(productcategoryid as integer) as productcategoryid,
        name
    """,
    "productcategory": """
        cast(productcategoryid as integer) as productcategoryid,
        name
    """,
    "address": """
        cast(addressid as integer) as addressid,
        addressline1,
        city,
        cast(stateprovinceid as integer) as stateprovinceid,
        postalcode
    """,
    "stateprovince": """
        cast(stateprovinceid as integer) as stateprovinceid,
        stateprovincecode,
        countryregioncode,
        name
    """,
    "countryregion": """
        countryregioncode,
        name
    """,
    "creditcard": """
        cast(creditcardid as integer) as creditcardid,
        cardtype,
        cardnumber,
        cast(expmonth as integer) as expmonth,
        cast(expyear as integer) as expyear
    """,
    "specialoffer": """
        cast(specialofferid as integer) as specialofferid,
        description,
        cast(discountpct as decimal(10, 4)) as discountpct,
        type,
        category
    """,
    "store": """
        cast(businessentityid as integer) as businessentityid,
        name
    """,
}


def download_zip(dest: Path) -> None:
    """Fetch the Microsoft OLTP zip (or reuse a local copy via the ``AW_OLTP_ZIP`` env var)."""
    local = os.environ.get("AW_OLTP_ZIP")
    if local:
        print(f"Using local zip from AW_OLTP_ZIP={local}")
        dest.write_bytes(Path(local).read_bytes())
        return
    print(f"Downloading {MS_ZIP_URL}")
    request = urllib.request.Request(MS_ZIP_URL, headers={"User-Agent": "adventureworks-loader"})
    with urllib.request.urlopen(request) as response:  # noqa: S310 - fixed https GitHub release URL
        dest.write_bytes(response.read())
    print(f"Downloaded {dest.stat().st_size:,} bytes")


def _varchar_columns(columns: list[str]) -> str:
    return "{" + ", ".join(f"'{name}': 'VARCHAR'" for name in columns) + "}"


def stage_raw(con: duckdb.DuckDBPyConnection, table: str, csv_path: Path) -> None:
    """Load a source CSV into an all-VARCHAR staging relation named ``raw_<table>``."""
    columns = _varchar_columns(RAW_COLUMNS[table])
    if table == "person":
        # Person uses "+|" field / "&|\n" row terminators (XML columns can contain tabs/newlines).
        rows = _parse_person(csv_path)
        con.execute(
            f"create table raw_{table} (businessentityid varchar, firstname varchar, "
            "lastname varchar, persontype varchar)"
        )
        con.executemany(f"insert into raw_{table} values (?, ?, ?, ?)", rows)
        return
    if table == "store":
        # Store also uses "+|" / "&|\n" terminators (Demographics is XML like Person).
        rows = _parse_store(csv_path)
        con.execute(f"create table raw_{table} (businessentityid varchar, name varchar)")
        con.executemany(f"insert into raw_{table} values (?, ?)", rows)
        return
    con.execute(
        f"create table raw_{table} as "
        f"select * from read_csv(?, delim='{TAB}', header=false, quote='', columns={columns})",
        [str(csv_path)],
    )


def _parse_person(csv_path: Path) -> list[tuple[str, str, str, str]]:
    """Parse the ``+|`` / ``&|`` delimited Person.csv into (businessentityid, first, last, type)."""
    text = csv_path.read_text(encoding="utf-8", errors="replace")
    rows: list[tuple[str, str, str, str]] = []
    for record in text.split("&|\n"):
        if not record:
            continue
        fields = record.split("+|")
        rows.append((fields[0], fields[4], fields[6], fields[1]))
    return rows


def _parse_store(csv_path: Path) -> list[tuple[str, str]]:
    """Parse the ``+|`` / ``&|`` delimited Store.csv into (businessentityid, name)."""
    text = csv_path.read_text(encoding="utf-8", errors="replace")
    rows: list[tuple[str, str]] = []
    for record in text.split("&|\n"):
        if not record:
            continue
        fields = record.split("+|")
        rows.append((fields[0], fields[1]))
    return rows


def derive_offset_days(con: duckdb.DuckDBPyConnection) -> int:
    """Derive the uniform date-shift offset and assert the span guard (reversible shift)."""
    row = con.execute(
        "select min(cast(orderdate as timestamp)::date), max(cast(orderdate as timestamp)::date) "
        "from raw_salesorderheader"
    ).fetchone()
    assert row is not None
    min_date, max_date = row
    span = (max_date - min_date).days
    if span != CANONICAL_ORDER_DATE_SPAN_DAYS:
        raise RuntimeError(
            f"Unexpected OrderDate span {span} days (expected {CANONICAL_ORDER_DATE_SPAN_DAYS}); "
            "the release layout changed -- refusing to guess the date shift."
        )
    offset = (min_date - CANONICAL_FIRST_ORDER_DATE).days
    print(f"Derived date-shift offset: {offset} days ({min_date} -> {CANONICAL_FIRST_ORDER_DATE})")
    return offset


def write_parquet(con: duckdb.DuckDBPyConnection, table: str, offset_days: int) -> int:
    """Project the typed, in-scope columns and write ``data/adventure_works/<table>.parquet``."""
    projection = PROJECTIONS[table].format(offset=offset_days)
    out_path = OUTPUT_DIR / f"{table}.parquet"
    con.execute(
        f"copy (select {projection} from raw_{table}) "
        f"to '{out_path}' (format parquet, compression zstd)"
    )
    count = con.execute(f"select count(*) from raw_{table}").fetchone()
    assert count is not None
    return int(count[0])


def assert_reconciliation(con: duckdb.DuckDBPyConnection) -> None:
    """Oracle: 2011 gross (all sales) = sum(unitprice * orderqty) must equal the audited figure."""
    row = con.execute(
        """
        select round(sum(d.unitprice * d.orderqty), 2)
        from read_parquet(?) as d
        join read_parquet(?) as h on d.salesorderid = h.salesorderid
        where year(h.orderdate) = 2011
        """,
        [
            str(OUTPUT_DIR / "salesorderdetail.parquet"),
            str(OUTPUT_DIR / "salesorderheader.parquet"),
        ],
    ).fetchone()
    assert row is not None
    actual = Decimal(str(row[0]))
    print(f"2011 gross (all sales): {actual}")
    if actual != EXPECTED_2011_GROSS:
        raise RuntimeError(
            f"2011 reconciliation FAILED: got {actual}, expected {EXPECTED_2011_GROSS}. "
            "The loaded data does not match the audited AdventureWorks figure."
        )
    print(f"Reconciliation OK: 2011 gross == {EXPECTED_2011_GROSS}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / "adventureworks-oltp.zip"
        download_zip(zip_path)
        with zipfile.ZipFile(zip_path) as archive:
            for filename in CSV_FILENAME.values():
                archive.extract(filename, tmp_path)

        con = duckdb.connect()
        for table in RAW_COLUMNS:
            stage_raw(con, table, tmp_path / CSV_FILENAME[table])

        offset_days = derive_offset_days(con)
        for table in RAW_COLUMNS:
            rows = write_parquet(con, table, offset_days)
            print(f"  wrote {table}.parquet ({rows:,} rows)")

        assert_reconciliation(con)
    print(f"Done. Parquet source-of-record in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
