"""Ledger store CRUD tests."""

from apex_ledger.ledger.store import LedgerStore


def test_holdings_crud_and_personal_mode(tmp_path):
    store = LedgerStore(tmp_path / "ledger.db")
    store.seed_demo_data()
    assert store.is_demo_portfolio()

    store.clear_portfolio()
    hid = store.add_holding("vti", 10, 2500, "brokerage")
    assert store.list_holdings()[0].id == hid
    assert store.list_holdings()[0].symbol == "VTI"
    assert not store.is_demo_portfolio()

    store.update_holding(hid, "BND", 5, 400, "brokerage")
    assert store.list_holdings()[0].symbol == "BND"

    store.delete_holding(hid)
    assert store.list_holdings() == []


def test_transaction_add(tmp_path):
    from datetime import date

    store = LedgerStore(tmp_path / "ledger.db")
    tid = store.add_transaction(date(2026, 5, 1), "Coffee", -4.5, "checking")
    txs = store.list_transactions()
    assert txs[0].id == tid
    assert txs[0].amount == -4.5
