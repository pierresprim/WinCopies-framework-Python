"""ORM DELETE — test matrix (SQLite reference).

Each scenario runs on a fresh in-memory DB (or a temp file for RowVanished).
Reports PASS/FAIL per scenario; does not attempt to fix the ORM on failure.

Covers spec 12.1 §B.7: nominal delete, composite PK, DB-origin vs
App-origin-promoted, reads post-delete, the guards, rollback=revert (INSERT
family), re-insertion rejection (root / DB-origin / FK target), and a mixed
update+delete rollback.
"""
import os, sqlite3, tempfile, traceback

from WinCopies.Typing.Delegate import Action, IStruct, Struct
from WinCopies.Data.Abstract import IConnection, IDataBase
from WinCopies.Data.Factory import IFieldFactory
from WinCopies.Data.Field import FieldAttributes, IntegerMode, TextMode, IntegerField, TextField
from WinCopies.Data.ORM import (ITransaction, DataContextBase, DataContext, Entity, EntityCollection,
                                autoPrimaryKeyConfig, primaryKeyConfig, columnConfig, entityColumnConfig,
                                PrimaryKeyMutationError, RowVanishedError, UnresolvedRollbackError,
                                EntityNotPersistedError, DeletedEntityError, InvalidOperationError)
from WinCopies.Data.SQLite import Connection

# ------------------------------------------------------------------ entities
class Item(Entity):
    def __init__(self, quantity: int) -> None:
        super().__init__()

        self.__id: IStruct[int] = Struct[int](0)
        self.__quantity: IStruct[int] = Struct[int](quantity)

    def Dispose(self) -> None: pass

    @autoPrimaryKeyConfig()
    def Id(self) -> IStruct[int]: return self.__id

    @columnConfig()
    def Quantity(self) -> IStruct[int]: return self.__quantity

    def _SetIdRaw(self, v: int) -> None: self.__id.SetValue(v)   # test-only: bypass the read-only PK
class Items(EntityCollection[Item]):
    def __init__(self, c: DataContextBase) -> None: super().__init__(c)

    def _GetType(self) -> type[Item]: return Item

class Line(Entity):
    def __init__(self, o: int, l: int, q: int) -> None:
        super().__init__()

        self.__o: IStruct[int] = Struct[int](o); self.__l: IStruct[int] = Struct[int](l); self.__q: IStruct[int] = Struct[int](q)

    def Dispose(self) -> None: pass

    @primaryKeyConfig()
    def OrderId(self) -> IStruct[int]: return self.__o

    @primaryKeyConfig()
    def LineId(self) -> IStruct[int]: return self.__l

    @columnConfig()
    def Quantity(self) -> IStruct[int]: return self.__q
class Lines(EntityCollection[Line]):
    def __init__(self, c: DataContextBase) -> None: super().__init__(c)
    def _GetType(self) -> type[Line]: return Line

class Category(Entity):
    def __init__(self, name: str) -> None:
        super().__init__()

        self.__id: IStruct[int] = Struct[int](0); self.__name: IStruct[str] = Struct[str](name)

    def Dispose(self) -> None: pass

    @autoPrimaryKeyConfig()
    def Id(self) -> IStruct[int]: return self.__id

    @columnConfig()
    def Name(self) -> IStruct[str]: return self.__name
class Categories(EntityCollection[Category]):
    def __init__(self, c: DataContextBase) -> None: super().__init__(c)
    def _GetType(self) -> type[Category]: return Category

class Product(Entity):
    def __init__(self, price: int, category: Category) -> None:
        super().__init__()

        self.__id: IStruct[int] = Struct[int](0); self.__price: IStruct[int] = Struct[int](price)
        self.__category: IStruct[Category] = Struct[Category](category)

    def Dispose(self) -> None: pass

    @autoPrimaryKeyConfig()
    def Id(self) -> IStruct[int]: return self.__id

    @columnConfig()
    def Price(self) -> IStruct[int]: return self.__price

    @entityColumnConfig(Category)
    def Category(self) -> IStruct["Category"]: return self.__category
class Products(EntityCollection[Product]):
    def __init__(self, c: DataContextBase) -> None: super().__init__(c)

    def _GetType(self) -> type[Product]: return Product

# ------------------------------------------------------------------ helpers
def delete(e: Entity) -> Action:
    def d(e: Entity) -> None: e.Delete()

    return lambda: d(e)

def is_deleted(e: Entity) -> bool: return e._IsDeleted() # pyright: ignore[reportPrivateUsage]
def is_persisted(ctx: DataContextBase, e: Entity) -> bool: return ctx._IsInstancePersisted(e) # pyright: ignore[reportPrivateUsage]

def make_conn(path: str = ":memory:") -> IConnection:
    conn = Connection(path)

    conn.Open()

    return conn

def col(ff: IFieldFactory, name: str) -> IntegerField: return ff.CreateInteger(name, FieldAttributes(0), IntegerMode.Long) # plain integer column (NOT NULL; value supplied)
def pk(ff: IFieldFactory, name: str) -> IntegerField: return ff.CreateInteger(name, FieldAttributes.PrimaryKey, IntegerMode.Long) # auto-increment integer primary key
def txt(ff: IFieldFactory, name: str) -> TextField: return ff.CreateText(name, FieldAttributes(0), TextMode.Text) # plain text column

def create_item_table(conn: IConnection) -> None:
    db: IDataBase = conn.GetCursor()
    ff: IFieldFactory = conn.GetFactoryProvider().GetFieldFactory()

    db.CreateTable("Item", (pk(ff, "Id"), col(ff, "Quantity")))

def insert_item(ctx: DataContextBase, q: int) -> Item:
    it = Item(q)
    tx = ctx.BeginTransaction()

    assert tx.TryAdd(it) is True; tx.Dispose()

    return it

def item_rows(conn: IConnection) -> list[tuple[int, int]]:
    return [(r.Id, r.Quantity) for r in Items(DataContext(conn)).Select().AsIterable()]

_results: list[tuple[str, bool, str]] = []

def scenario(name: str, fn: Action) -> None:
    try:
        fn()

        _results.append((name, True, "")); print(f"[PASS] {name}")
    except AssertionError as e:
        _results.append((name, False, f"assert: {e}")); print(f"[FAIL] {name}: assert: {e}")
    except BaseException as e:
        _results.append((name, False, f"{type(e).__name__}: {e}")); print(f"[ERR ] {name}: {type(e).__name__}: {e}")
        traceback.print_exc()

def expect_raises(exc_type: type[Exception], fn: Action) -> None:
    try: fn()
    except exc_type: return

    except BaseException as e: raise AssertionError(f"expected {exc_type.__name__}, got {type(e).__name__}: {e}")

    raise AssertionError(f"expected {exc_type.__name__}, nothing raised")

# ------------------------------------------------------------------ scenarios
def s_simple() -> None:
    # nominal delete: row absent after commit, entity tombstoned, unpersisted; reads still work.
    conn = make_conn()

    create_item_table(conn)

    ctx = DataContext(conn)
    it = insert_item(ctx, 10)

    tx = ctx.BeginTransaction()
    it.Delete()
    tx.Dispose()

    assert item_rows(conn) == [], item_rows(conn)      # row gone from DB (a re-query no longer yields it)
    assert is_deleted(it), "entity must be tombstoned"
    assert not is_persisted(ctx, it), "entity must no longer be persisted"
    # reads post-delete: last value kept, PK not nulled
    assert it.Quantity == 10, f"leave-as-is on values: expected 10, got {it.Quantity}"
    assert it.Id == 1, f"PK must not be nulled, got {it.Id}"

def s_composite() -> None:
    # composite PK: WHERE (OrderId = ?) AND (LineId = ?) must target exactly one of two rows.
    conn = make_conn()
    ff = conn.GetFactoryProvider().GetFieldFactory()

    conn.GetCursor().CreateTable("Line", [col(ff, "OrderId"), col(ff, "LineId"), col(ff, "Quantity")], None)

    ctx = DataContext(conn)
    a = Line(10, 5, 100); b = Line(10, 6, 200)

    tx = ctx.BeginTransaction(); assert tx.TryAdd(a) is True; assert tx.TryAdd(b) is True; tx.Dispose()

    tx = ctx.BeginTransaction(); a.Delete(); tx.Dispose()

    rows = [(r.OrderId, r.LineId, r.Quantity) for r in Lines(DataContext(conn)).Select().AsIterable()]

    assert rows == [(10, 6, 200)], rows                 # only the targeted row was deleted

def s_db_origin() -> None:
    # delete a DB-origin (hydrated) entity: wasPersisted == False, tombstones correctly.
    conn = make_conn()

    create_item_table(conn)

    insert_item(DataContext(conn), 10)                  # persisted+committed via a first context

    ctx = DataContext(conn)                             # fresh context: re-hydrate from DB (DB-origin cookie)
    it = list(Items(ctx).Select().AsIterable())[0]

    assert not is_persisted(ctx, it), "hydrated entity is not in __persisted"

    tx = ctx.BeginTransaction(); it.Delete(); tx.Dispose()

    assert is_deleted(it), "DB-origin entity must tombstone"
    assert item_rows(conn) == [], item_rows(conn)

def s_app_origin_promoted() -> None:
    # delete an App-origin entity inserted+committed in a prior tx: wasPersisted == True.
    conn = make_conn()

    create_item_table(conn)

    ctx = DataContext(conn)
    it = insert_item(ctx, 10)

    assert is_persisted(ctx, it), "promoted insert must be persisted"

    tx = ctx.BeginTransaction(); it.Delete(); tx.Dispose()

    assert is_deleted(it), "App-origin-promoted entity must tombstone"
    assert not is_persisted(ctx, it), "delete must unmark persisted"
    assert item_rows(conn) == [], item_rows(conn)

def s_guard_tombstone() -> None:
    conn = make_conn(); create_item_table(conn); ctx = DataContext(conn)
    it = insert_item(ctx, 10)
    tx = ctx.BeginTransaction(); it.Delete(); tx.Dispose()
    expect_raises(DeletedEntityError, delete(it))       # second Delete on a tombstone

def s_guard_transient() -> None:
    conn = make_conn(); create_item_table(conn); DataContext(conn)
    it = Item(10)                                       # never persisted -> no context handle
    expect_raises(EntityNotPersistedError, delete(it))

def s_guard_pk_drift() -> None:
    conn = make_conn(); create_item_table(conn); ctx = DataContext(conn)
    it = insert_item(ctx, 10)
    it._SetIdRaw(99) # pyright: ignore[reportPrivateUsage] # drift the primary key (struct bypass)
    tx = ctx.BeginTransaction()
    expect_raises(PrimaryKeyMutationError, delete(it))
    tx.Dispose()

def s_guard_row_vanished() -> None:
    path = tempfile.mkstemp(suffix=".db")[1]

    try:
        conn = make_conn(path); create_item_table(conn); ctx = DataContext(conn)
        it = insert_item(ctx, 10)
        # out-of-band deletion via a separate connection -> DELETE affects 0 rows
        raw = sqlite3.connect(path); raw.execute('DELETE FROM "Item" WHERE "Id" = 1'); raw.commit(); raw.close()
        tx = ctx.BeginTransaction()
        expect_raises(RowVanishedError, delete(it))
        tx.Dispose()

    finally:
        if os.path.exists(path): os.remove(path)

def s_guard_no_tx() -> None:
    conn = make_conn(); create_item_table(conn); ctx = DataContext(conn)
    it = insert_item(ctx, 10)                           # persisted, but no active tx after Dispose
    expect_raises(InvalidOperationError, delete(it))

def s_guard_blocked() -> None:
    # a rolled-back UPDATE arms the context; a subsequent DELETE must hit the gate (C1).
    conn = make_conn(); create_item_table(conn); ctx = DataContext(conn)
    it = insert_item(ctx, 10)
    it.Quantity = 20
    tx = ctx.BeginTransaction(); assert it.TryUpdate() is True; tx.Rollback(); tx.Dispose()
    assert ctx.IsBlocked(), "rolled-back update must arm the context"
    expect_raises(UnresolvedRollbackError, delete(it))

def s_rollback_revert() -> None:
    # delete then rollback -> entity restored (revert family), DB row present, no block; re-delete works.
    conn = make_conn(); create_item_table(conn); ctx = DataContext(conn)
    it = insert_item(ctx, 10)

    tx = ctx.BeginTransaction(); it.Delete(); tx.Rollback(); tx.Dispose()

    assert not is_deleted(it), "rollback must un-tombstone"
    assert is_persisted(ctx, it), "rollback must restore persisted (wasPersisted was True)"
    assert not ctx.IsBlocked(), "delete rollback must NOT arm the block (restoration, not leave-as-is)"
    assert item_rows(conn) == [(1, 10)], item_rows(conn) # DB row still present

    tx = ctx.BeginTransaction(); it.Delete(); tx.Dispose()   # a re-delete re-emits cleanly
    assert item_rows(conn) == [], item_rows(conn)

def s_reinsert_root_app() -> None:
    # TryAdd of a tombstoned App-origin entity (as root) -> DeletedEntityError.
    conn = make_conn(); create_item_table(conn); ctx = DataContext(conn)
    it = insert_item(ctx, 10)
    tx = ctx.BeginTransaction(); it.Delete(); tx.Dispose()
    tx = ctx.BeginTransaction()
    expect_raises(DeletedEntityError, lambda: tx.TryAdd(it))
    tx.Dispose()

def s_reinsert_root_db_origin() -> None:
    # THE head-guard test: a tombstoned DB-origin entity must RAISE on re-add, not be silently
    # skipped by the DataBase-origin branch of _TryAdd.
    conn = make_conn(); create_item_table(conn)
    insert_item(DataContext(conn), 10)
    ctx = DataContext(conn)
    it = list(Items(ctx).Select().AsIterable())[0]      # DB-origin
    tx = ctx.BeginTransaction(); it.Delete(); tx.Dispose()
    tx = ctx.BeginTransaction()
    expect_raises(DeletedEntityError, lambda: tx.TryAdd(it))
    tx.Dispose()

def s_reinsert_fk_target() -> None:
    # TryAdd of a Product whose entity-column points at a tombstoned Category -> DeletedEntityError
    # (the guard fires on the FK edge during recursive enumeration).
    conn = make_conn()
    ff = conn.GetFactoryProvider().GetFieldFactory()
    db = conn.GetCursor()

    db.CreateTable("Category", [pk(ff, "Id"), txt(ff, "Name")], None)
    db.CreateTable("Product", [pk(ff, "Id"), col(ff, "Price"), col(ff, "Category")], None)

    ctx = DataContext(conn)
    c = Category("A")
    tx = ctx.BeginTransaction(); assert tx.TryAdd(c) is True; tx.Dispose()
    tx = ctx.BeginTransaction(); c.Delete(); tx.Dispose()   # tombstone the category

    p = Product(100, c)                                     # new product pointing at the tombstone
    tx = ctx.BeginTransaction()
    expect_raises(DeletedEntityError, lambda: tx.TryAdd(p))
    tx.Dispose()

def s_mixed_tx() -> None:
    # e1.TryUpdate(); e2.Delete() rolled back: block armed by the update alone; e2 restored.
    conn = make_conn(); create_item_table(conn); ctx = DataContext(conn)
    e1 = insert_item(ctx, 10); e2 = insert_item(ctx, 20)

    e1.Quantity = 11

    tx = ctx.BeginTransaction()
    assert e1.TryUpdate() is True
    e2.Delete()
    tx.Rollback(); tx.Dispose()

    assert ctx.IsBlocked(), "the update must arm the block"
    assert not is_deleted(e2), "the delete must be reverted (e2 restored)"
    assert is_persisted(ctx, e2), "e2 persisted must be restored"
    rows = dict(item_rows(conn))
    assert rows.get(2) == 20, f"e2's row must remain present, rows={rows}"

# ------------------------------------------------------------------ run
for name, fn in (
    ("simple delete persists", s_simple),
    ("composite-PK delete", s_composite),
    ("DB-origin delete (wasPersisted False)", s_db_origin),
    ("App-origin-promoted delete (wasPersisted True)", s_app_origin_promoted),
    ("guard: tombstone -> DeletedEntityError", s_guard_tombstone),
    ("guard: transient -> EntityNotPersistedError", s_guard_transient),
    ("guard: PK drift -> PrimaryKeyMutationError", s_guard_pk_drift),
    ("guard: row vanished -> RowVanishedError", s_guard_row_vanished),
    ("guard: no active tx -> InvalidOperationError", s_guard_no_tx),
    ("guard: blocked context -> UnresolvedRollbackError", s_guard_blocked),
    ("rollback = revert (restore, no block, re-delete)", s_rollback_revert),
    ("re-insert rejected: root (App-origin)", s_reinsert_root_app),
    ("re-insert rejected: root (DB-origin, head guard)", s_reinsert_root_db_origin),
    ("re-insert rejected: FK target", s_reinsert_fk_target),
    ("mixed update+delete rollback", s_mixed_tx)):

    scenario(name, fn)

print("\n==== SUMMARY ====")

passed = sum(1 for _, ok, _ in _results if ok)

for name, ok, msg in _results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   [{msg}]" if not ok else ""))

print(f"\n{passed}/{len(_results)} passed")
