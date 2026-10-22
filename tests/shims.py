"""Atlas Library - Test Ortamı Uyumluluk Katmanı (Compatibility Shims).

Bu modül, dış bağımlılıkların (pandas, streamlit) kurulu olmadığı ortamlarda
tüm testlerin ve Bekçi sistemlerinin %100 yerel ve bağımsız çalışabilmesini sağlar.
Eğer gerçek paketler kuruluysa doğrudan orijinal kütüphaneler kullanılır.
"""

from __future__ import annotations

import sys
import types
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple


def _ensure_shims() -> None:
    # 1. Streamlit Shim
    if "streamlit" not in sys.modules:
        try:
            import streamlit
        except ImportError:
            st_mock = types.ModuleType("streamlit")

            class SessionState(dict):
                def __getattr__(self, item):
                    return self.get(item)
                def __setattr__(self, key, value):
                    self[key] = value

            st_mock.session_state = SessionState()
            st_mock.secrets = {}

            def _dec(*args, **kwargs):
                def _wrap(f):
                    f.clear = lambda: None
                    return f
                return _wrap if args and not callable(args[0]) else _wrap(args[0]) if args else _wrap

            st_mock.cache_data = _dec
            st_mock.cache_resource = _dec
            st_mock.dialog = lambda *a, **k: _dec
            st_mock.fragment = lambda *a, **k: _dec

            st_mock.markdown = lambda *a, **k: None
            st_mock.caption = lambda *a, **k: None
            st_mock.info = lambda *a, **k: None
            st_mock.success = lambda *a, **k: None
            st_mock.warning = lambda *a, **k: None
            st_mock.error = lambda *a, **k: None
            st_mock.toast = lambda *a, **k: None
            st_mock.balloons = lambda *a, **k: None
            st_mock.write = lambda *a, **k: None
            st_mock.image = lambda *a, **k: None
            st_mock.metric = lambda *a, **k: None
            st_mock.progress = lambda *a, **k: None
            st_mock.set_page_config = lambda *a, **k: None
            st_mock.rerun = lambda *a, **k: None
            st_mock.stop = lambda *a, **k: None

            class MockCol:
                def __enter__(self): return self
                def __exit__(self, *a): pass
                def markdown(self, *a, **k): pass
                def metric(self, *a, **k): pass
                def button(self, *a, **k): return False
                def checkbox(self, *a, **k): return False
                def write(self, *a, **k): pass
                def caption(self, *a, **k): pass
                def text_input(self, *a, **k): return ""

            st_mock.columns = lambda n: [MockCol() for _ in range(n if isinstance(n, int) else len(n))]
            st_mock.container = lambda *a, **k: MockCol()
            st_mock.expander = lambda *a, **k: MockCol()
            st_mock.form = lambda *a, **k: MockCol()
            st_mock.form_submit_button = lambda *a, **k: False
            st_mock.button = lambda *a, **k: False
            st_mock.text_input = lambda *a, **k: k.get("value", "")
            st_mock.text_area = lambda *a, **k: k.get("value", "")
            st_mock.number_input = lambda *a, **k: k.get("value", 1)
            st_mock.selectbox = lambda *a, **k: a[1][0] if len(a) > 1 and a[1] else (k.get("options", [""])[0] if k.get("options") else "")
            st_mock.multiselect = lambda *a, **k: k.get("default", [])
            st_mock.checkbox = lambda *a, **k: k.get("value", False)
            st_mock.slider = lambda *a, **k: k.get("value", 5)
            st_mock.dataframe = lambda *a, **k: None
            st_mock.data_editor = lambda df, *a, **k: df
            st_mock.download_button = lambda *a, **k: False

            comp_v1 = types.ModuleType("streamlit.components.v1")
            comp_v1.html = lambda *a, **k: None
            st_mock.components = types.ModuleType("streamlit.components")
            st_mock.components.v1 = comp_v1

            class MockPage:
                def __init__(self, page, title=None, icon=None, default=False):
                    self.page = page
                    self.title = title
                    self.icon = icon
                    self.default = default

            st_mock.Page = MockPage

            class MockNav:
                def __init__(self, pages): self.pages = pages
                def run(self): pass

            st_mock.navigation = MockNav
            sys.modules["streamlit"] = st_mock
            sys.modules["streamlit.components"] = st_mock.components
            sys.modules["streamlit.components.v1"] = comp_v1

    # 2. Pandas Shim
    if "pandas" not in sys.modules:
        try:
            import pandas
        except ImportError:
            pd_mock = types.ModuleType("pandas")

            class Series:
                def __init__(self, data, index=None):
                    if isinstance(data, dict):
                        self.index = list(data.keys())
                        self._data = list(data.values())
                        self._dict = dict(data)
                    elif isinstance(data, (str, bytes)) or not hasattr(data, "__iter__"):
                        if index is not None:
                            self._data = [data] * len(index)
                            self.index = list(index)
                        else:
                            self._data = [data]
                            self.index = [0]
                        self._dict = {i: v for i, v in zip(self.index, self._data)}
                    else:
                        self._data = list(data)
                        self.index = list(index if index is not None else range(len(self._data)))
                        self._dict = {i: v for i, v in zip(self.index, self._data)}

                def __len__(self):
                    return len(self._data)

                def __iter__(self):
                    return iter(self._data)

                @property
                def values(self):
                    return list(self._data)

                @property
                def empty(self):
                    return len(self._data) == 0

                def items(self):
                    for k, v in zip(self.index, self._data):
                        yield k, v

                def __getitem__(self, item):
                    if isinstance(item, str):
                        return self._dict.get(item)
                    if isinstance(item, int):
                        if 0 <= item < len(self._data):
                            return self._data[item]
                        return self._dict.get(item)
                    if isinstance(item, Series):
                        return Series([d for d, m in zip(self._data, item._data) if m],
                                      [i for i, m in zip(self.index, item._data) if m])
                    return self._data[item]

                def __setitem__(self, key, value):
                    if isinstance(key, str) and key in self.index:
                        idx = self.index.index(key)
                        self._data[idx] = value
                        self._dict[key] = value

                def __eq__(self, other):
                    if isinstance(other, Series):
                        return Series([a == b for a, b in zip(self._data, other._data)], self.index)
                    return Series([a == other for a in self._data], self.index)

                def __ne__(self, other):
                    if isinstance(other, Series):
                        return Series([a != b for a, b in zip(self._data, other._data)], self.index)
                    return Series([a != other for a in self._data], self.index)

                def __gt__(self, other):
                    return Series([x is not None and x > other for x in self._data], self.index)

                def __ge__(self, other):
                    return Series([x is not None and x >= other for x in self._data], self.index)

                def __lt__(self, other):
                    return Series([x is not None and x < other for x in self._data], self.index)

                def __le__(self, other):
                    return Series([x is not None and x <= other for x in self._data], self.index)

                def __and__(self, other):
                    return Series([bool(a and b) for a, b in zip(self._data, other._data)], self.index)

                def __or__(self, other):
                    return Series([bool(a or b) for a, b in zip(self._data, other._data)], self.index)

                def __invert__(self):
                    return Series([not bool(a) for a in self._data], self.index)

                def isin(self, values):
                    s = set(values)
                    return Series([a in s for a in self._data], self.index)

                def map(self, fn):
                    return Series([fn(x) for x in self._data], self.index)

                def fillna(self, val):
                    return Series([val if x is None or (isinstance(x, float) and x != x) or x == "" else x for x in self._data], self.index)

                def astype(self, t):
                    return Series([t(x) if x is not None else x for x in self._data], self.index)

                def sum(self):
                    return sum(1 for x in self._data if x)

                def value_counts(self):
                    counts = {}
                    for x in self._data:
                        counts[x] = counts.get(x, 0) + 1
                    return Series(list(counts.values()), index=list(counts.keys()))

                @property
                def str(self):
                    parent = self
                    class StrAccessor:
                        def contains(self, pat, case=True, na=False):
                            p = pat if case else pat.lower()
                            res = []
                            for x in parent._data:
                                if x is None:
                                    res.append(na)
                                else:
                                    s = str(x) if case else str(x).lower()
                                    res.append(p in s)
                            return Series(res, parent.index)
                    return StrAccessor()

            class ILocIndexer:
                def __init__(self, df):
                    self.df = df
                def __getitem__(self, item):
                    if isinstance(item, int):
                        return Series(self.df._rows[item])
                    if isinstance(item, slice):
                        start = item.start or 0
                        stop = item.stop if item.stop is not None else len(self.df._rows)
                        return DataFrame(self.df._rows[start:stop])
                    return self.df

            class DataFrame:
                def __init__(self, data=None, columns=None):
                    if data is None:
                        self._rows = []
                    elif isinstance(data, list):
                        self._rows = [dict(r) if hasattr(r, "keys") else dict(r) for r in data]
                    elif isinstance(data, dict):
                        keys = list(data.keys())
                        n = len(data[keys[0]]) if keys else 0
                        self._rows = [{k: data[k][i] for k in keys} for i in range(n)]
                    elif isinstance(data, DataFrame):
                        self._rows = [dict(r) for r in data._rows]
                    else:
                        self._rows = list(data)

                def __len__(self):
                    return len(self._rows)

                @property
                def empty(self):
                    return len(self._rows) == 0

                @property
                def columns(self):
                    if not self._rows:
                        return []
                    return list(self._rows[0].keys())

                @property
                def index(self):
                    return list(range(len(self._rows)))

                @property
                def iloc(self):
                    return ILocIndexer(self)

                def __getitem__(self, item):
                    if isinstance(item, str):
                        return Series([r.get(item) for r in self._rows], self.index)
                    if isinstance(item, Series):
                        return DataFrame([r for r, m in zip(self._rows, item._data) if m])
                    return self._rows[item]

                def __setitem__(self, key, value):
                    if isinstance(value, Series):
                        vals = value._data
                    elif isinstance(value, list):
                        vals = value
                    else:
                        vals = [value] * len(self._rows)
                    for r, v in zip(self._rows, vals):
                        r[key] = v

                def copy(self):
                    return DataFrame([dict(r) for r in self._rows])

                def sort_values(self, by, ascending=True):
                    keys = [by] if isinstance(by, str) else list(by)
                    def sort_key(r):
                        return tuple(r.get(k) or "" for k in keys)
                    sorted_rows = sorted(self._rows, key=sort_key, reverse=not ascending)
                    return DataFrame(sorted_rows)

                def iterrows(self):
                    for idx, r in enumerate(self._rows):
                        yield idx, Series(r)

                def to_dict(self, orient="records"):
                    return [dict(r) for r in self._rows]

                def sample(self, n=1):
                    import random
                    n = min(n, len(self._rows))
                    if n <= 0:
                        return DataFrame([])
                    return DataFrame(random.sample(self._rows, n))

                def groupby(self, col):
                    groups = {}
                    for r in self._rows:
                        key = r.get(col)
                        groups.setdefault(key, []).append(r)

                    class GroupByObj:
                        def agg(self, **kwargs):
                            out_rows = []
                            for k, g in groups.items():
                                row = {col: k}
                                for out_k, (src_col, agg_fn) in kwargs.items():
                                    vals = [item.get(src_col) for item in g]
                                    if agg_fn == "count":
                                        row[out_k] = len(vals)
                                    elif callable(agg_fn):
                                        row[out_k] = agg_fn(Series(vals))
                                    else:
                                        row[out_k] = len(vals)
                                out_rows.append(row)
                            class AggResult(DataFrame):
                                def reset_index(self): return self
                            return AggResult(out_rows)

                        def __iter__(self):
                            for k, g in groups.items():
                                yield k, DataFrame(g)

                    return GroupByObj()

                def insert(self, loc, column, value):
                    vals = value if isinstance(value, list) else list(value)
                    for r, v in zip(self._rows, vals):
                        r[column] = v

            def to_numeric(arg, errors="coerce"):
                if isinstance(arg, Series):
                    res = []
                    for x in arg._data:
                        try:
                            res.append(float(x) if x is not None and str(x).strip() != "" else None)
                        except (ValueError, TypeError):
                            res.append(None)
                    return Series(res, arg.index)
                try:
                    return float(arg)
                except Exception:
                    return None

            def isna(arg):
                return arg is None or arg == "" or (isinstance(arg, float) and arg != arg)

            def notna(arg):
                return not isna(arg)

            def read_sql(sql, con):
                cursor = con.execute(sql)
                cols = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                data = [dict(zip(cols, r)) for r in rows]
                return DataFrame(data)

            def crosstab(s1, s2, **kw):
                return DataFrame([{"Dil": "Türkçe", "Toplam": 1}])

            pd_mock.DataFrame = DataFrame
            pd_mock.Series = Series
            pd_mock.to_numeric = to_numeric
            pd_mock.isna = isna
            pd_mock.notna = notna
            pd_mock.read_sql = read_sql
            pd_mock.crosstab = crosstab

            sys.modules["pandas"] = pd_mock


_ensure_shims()
